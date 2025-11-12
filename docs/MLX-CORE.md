## In-Depth Research Report: `mlx.core` Performance Optimization & Kernel Development

**Objective**
Provide a concrete technical foundation for maximizing performance of `mlx.core` on Apple Silicon, with a focus on:

* Understanding `mlx.core` execution and optimization model
* Designing data pipelines that play well with MLX and Apple’s unified memory
* Exploiting vectorization and parallelism
* Identifying when and how to use custom kernels (C++ / Metal)
* Establishing a reproducible profiling & benchmarking workflow for this repository

Target use cases include high-throughput RAG pipelines and generative workloads (e.g. FLUX txt2image) running locally on Apple Silicon.

---

## 1. `mlx.core` Execution Model & Best Practices

### 1.1 Lazy evaluation & computation graphs

`mlx.core` is built around **lazy evaluation**:

* Operations on `mx.array` objects build a computation graph instead of executing immediately.
* Actual execution happens only when values are required on the host:

  * `print(x)`
  * `x.item()`
  * `np.array(x)` / `x.tolist()`
  * `mx.eval(x)` or `mx.eval([x, y, ...])`

**Why this matters**

* The backend can analyze the graph and:

  * Fuse elementwise operations into fewer kernels.
  * Reorder some operations.
  * Avoid materializing useless intermediates.

**Practical rules**

* Prefer:

  * Building expression chains (`y = mx.maximum(mx.matmul(A, B) + bias, 0)`)
  * Executing with *explicit* `mx.eval` at logical boundaries (e.g. at the end of a forward pass).
* Avoid:

  * Interleaving Python control flow with eager host reads, e.g.:

    ```python
    # Bad: forces sync on every step
    for i in range(steps):
        y = step(x)
        mx.eval(y)       # sync every iteration
    ```

  * Frequent `.item()` or `np.array(x)` calls inside loops.

Instead, accumulate work in MLX and **only sync when you actually need data** (logging, loss scalars, etc.).

---

### 1.2 Idiomatic `mlx.core` vs Python anti-patterns

`mlx.core` is designed for **vectorized, array-wise operations**. The fastest code:

* Minimizes Python loops
* Avoids explicit per-element indexing
* Operates on full tensors or reasonably sized blocks

**Anti-pattern**

```python
# Non-idiomatic: CPU loop, no fusion
def relu_python(x_np):
    out = np.empty_like(x_np)
    for i in range(x_np.shape[0]):
        out[i] = max(x_np[i], 0)
    return out
```

**Idiomatic MLX**

```python
import mlx.core as mx

def relu_mlx(x: mx.array) -> mx.array:
    return mx.maximum(x, 0)

x = mx.random.normal((1000, 1000))
y = relu_mlx(x)
mx.eval(y)
```

This allows MLX to:

* Compile a single kernel for the ReLU op
* Vectorize over the entire array
* Potentially fuse with surrounding ops (`x * scale + bias`, etc.)

**Guideline:**
If you find yourself writing `for i in range(x.shape[0])` outside trivial glue code, stop and ask: *Can this be expressed as a single `mlx.core` operation on the full array?*

---

### 1.3 Streams & overlapping work

MLX exposes a **stream API** to manually manage execution streams:

* Conceptually similar to command queues:

  * You schedule operations onto a stream.
  * Different streams can execute concurrently when possible.
* This can be used to:

  * Overlap CPU preprocessing with GPU compute
  * Run independent compute branches in parallel

For now, the practical takeaway:

* Keep your high-level design amenable to **coarse-grained parallelism**:

  * Batch operations (e.g. score many documents at once in RAG).
  * Group independent computations into chunks that can be overlapped later if needed.

---

## 2. Data Layout, Memory Access & Precision

### 2.1 Data layout & contiguity

MLX uses **row-major (C-style)** layout by default:

* Contiguous dimensions matter for:

  * Cache locality
  * Memory coalescing on the GPU
  * Vectorized load/store instructions

**Rules of thumb**

* Respect expected layouts for primitives:

  * For convolution / vision ops, be consistent with the required layout (`NCHW` or `NHWC` depending on the specific layer implementation you’re using).
* Avoid unnecessary transposes:

  * Chain your operations to minimize layout changes.
  * If a transpose is required, keep it at predictable points, not repeatedly inside inner loops.

### 2.2 Unified memory on Apple Silicon

Apple Silicon uses a **unified memory architecture**:

* CPU & GPU share the same physical memory pool.
* You don’t explicitly “copy to GPU” like CUDA `cudaMemcpy` calls.

However:

* Uncoalesced, random access patterns are still slow.
* “Minimize copies” still matters: each extra materialization burns bandwidth.

**Practical consequences**

* Avoid repeatedly creating new arrays when simple in-place updates work and are semantically correct, e.g.:

  ```python
  # Better (when safe)
  x += 1

  # Worse
  x = x + 1
  ```

* Try to **reuse tensors** across steps when shapes/semantics allow it, especially for temporary buffers in hot paths (e.g. attention blocks, recurrent operations).

### 2.3 Data types: `float32` vs `bfloat16`

MLX supports lower-precision types that can significantly speed up compute:

* `float32`: baseline, safest for correctness.
* `bfloat16`: often a **very good trade-off** between precision and throughput for training/inference.
* `float16`: narrower exponent range; more likely to cause numerical issues depending on the workload.

**Plan for this repo**

* Implement a simple dtype switch in the Flux / RAG pipelines:

  * A config flag or env var: `MLX_DTYPE=float32|bfloat16`.
  * Convert inputs & model weights to the selected type at init time.
* Benchmark:

  * Forward latency
  * Memory usage
  * Output quality (e.g. small image / text quality sanity checks)

---

## 3. Vectorization & Parallel Execution Patterns

### 3.1 Design for large batches & full-tensor operations

The MLX backend is most effective when you give it:

* **Big, dense arrays**
* Well-structured operations (matmul, conv, attention, elementwise chains)

Examples of good patterns in this repo context:

* RAG:

  * Encode all candidate passages for a query as a single batch and score them together.
* FLUX / diffusion:

  * Operate on `[batch, channels, height, width]` tensors end-to-end without slicing them into per-sample operations in Python.

### 3.2 Typical “rewrite to vectorized” transformations

1. **Looping over time vs stacking along a new dimension**

   ```python
   # Before: T eager steps, each sync-heavy
   xs = []
   x = x0
   for t in range(T):
       x = step(x)
       xs.append(x)

   # After: design step() to accept an additional time dimension when possible,
   # or move the loop into MLX ops (scan-like structures, if supported).
   ```

2. **Masking instead of conditional Python logic**

   ```python
   # Before
   for i in range(N):
       if mask[i]:
           out[i] = fn(in_[i])
       else:
           out[i] = 0

   # After
   out = fn(in_)
   out = mx.where(mask, out, mx.zeros_like(out))
   ```

3. **Broadcasting instead of repeated expand / tile**

   * Prefer `x + bias` where `bias` has shape `(C,)` and broadcasts over batch/height/width.
   * Avoid manually `mx.tile` or `mx.concatenate` unless absolutely necessary.

---

## 4. Kernel Fusion & Custom Kernels

### 4.1 Why fusion matters

The two big performance killers are:

1. Kernel launch overhead
2. Writing intermediates back to main memory between ops

Given a naive chain:

```python
y = mx.matmul(x, W)
z = y + b
out = mx.maximum(z, 0)
```

Naive execution:

* Kernel 1: `matmul`
* Kernel 2: `add`
* Kernel 3: `relu`

Each step potentially reads/writes full tensors.

Fused kernel:

* Single kernel:

  * Load `x`, `W`, `b`
  * Compute `y = x @ W`
  * Add bias
  * Apply ReLU
  * Write final result only once

This reduces:

* Global memory traffic
* Kernel launch overhead
* Cache misses

### 4.2 What MLX does automatically

* Simple elementwise chains are typically fused automatically by the backend.
* Patterns like:

  ```python
  y = x * a + b
  ```

  can map to fused multiply-add (FMA) style kernels.

You still have to:

* Keep these chains **in a single expression** so that MLX can see them.
* Avoid breaking them with host syncs or unnecessary temporaries.

### 4.3 When custom kernels are justified

Consider writing custom kernels when all of these are true:

1. You’ve **profiled** and confirmed that:

   * A specific sequence of ops dominates runtime.
   * It doesn’t fuse automatically.
2. The pattern is **repeatable** and appears in critical paths.
3. The cost of complexity is justified by the expected speedup.

In this repo, likely candidates:

* In FLUX / diffusion:

  * Patterns like `MatMul → Bias → Activation → Dropout` in attention or MLP blocks.
* In RAG scoring:

  * Heavy similarity computations or custom scoring logic on large batches.

### 4.4 Integration pattern (high-level)

A typical custom kernel flow:

1. **Identify pattern** (e.g. `matmul + bias + gelu`).
2. **Write a reference implementation** in pure `mlx.core` (for correctness).
3. **Profile** to confirm it’s worth optimizing.
4. Implement:

   * A Metal kernel describing the fused operation.
   * Minimal C++ wrapper using the MLX extension mechanism (C++ side) to:

     * Register the op
     * Handle shapes, strides, and type dispatch
   * A Python wrapper that exposes `fused_op(x, W, b)` and falls back to the reference implementation if needed (e.g. unsupported dtype or shape).
5. **Test rigorously**:

   * Numerical consistency against the reference implementation
   * Performance in both microbenchmarks and full models.

---

## 5. Profiling & Benchmarking Methodology

### 5.1 Python-level profiling

**Note on Model Downloading:** The model loading utilities (`src/rag/models/flux/utils.py`) are configured to prioritize local models. To force a re-download from Hugging Face for profiling network I/O or ensuring a canonical model version, set the following environment variable before running any script:
`export MLX_PROFILE_FORCE_DOWNLOAD=1`

Use this to catch the **obvious** stuff first:

* `cProfile` / `profile` modules for whole scripts.
* `time.perf_counter()` for small timing blocks.

Example pattern:

```python
import time
import mlx.core as mx

def benchmark_step(step_fn, x, n_iters=50):
    # Warmup
    for _ in range(10):
        y = step_fn(x)
        mx.eval(y)

    start = time.perf_counter()
    for _ in range(n_iters):
        y = step_fn(x)
        mx.eval(y)
    end = time.perf_counter()

    print(f"Avg time per step: {(end - start) / n_iters:.6f} s")
```

Use this in microbenchmarks for kernels or specific layers.

### 5.2 Hardware-level profiling with Instruments

For Apple Silicon, **Instruments** is non-optional if you’re serious:

* **Metal System Trace**:

  * Shows command buffers, kernel executions, dependencies.
  * Lets you see:

    * If the GPU is idle.
    * How many kernels are launched per forward pass.
* **GPU Counters**:

  * Occupancy
  * Memory bandwidth
  * ALU utilization

Workflow:

1. Run your script (e.g. `uv run python -m rag.cli.interactive_rag --profile-flux`).
2. Attach Instruments with Metal System Trace.
3. Trigger a forward pass (or a few iterations).
4. Inspect:

   * Longest kernels
   * Frequency of launches
   * Gaps where GPU is idle

These observations feed directly into your **optimization hit list**.

### 5.3 Benchmarks directory

Establish a reproducible benchmark suite under:

* `benchmarks/`

Initial scripts:

1. `benchmarks/benchmark_flux_forward_pass.py`

   * Load Flux model in a fixed configuration.
   * Run a fixed number of forward passes with synthetic input.
   * Print average latency and standard deviation.
2. `benchmarks/benchmark_rag_query.py`

   * Run a full query → retrieval → reranking pipeline on a fixed corpus subset.
   * Measure p95 latency and throughput.

These benchmarks become:

* The baseline before MLX-specific optimizations
* The regression checks after kernel / code changes

---

## 6. Actionable Plan for This Repository (MLX Acceleration)

This is the part you actually build.

### 6.1 Step 1: Profiling & bottleneck identification

**Status: Partially Done**
- Python-level profiling: **Complete**.
- GPU-level profiling: **Pending real Metal trace analysis.**

**Goal**
Identify the top GPU kernels and Python hot spots for:

* FLUX txt2image path
* RAG query path

**Tasks**

1. Add a simple `--profile` flag to the relevant CLIs:

   * `rag.cli.interactive_rag`
   * `flux_txt2image.py` (or equivalent)
2. Run representative workloads while:

   * Capturing `cProfile` output
   * Attaching Instruments with Metal System Trace
3. Produce a short report:

   * Top 5 GPU kernels by time
   * Top Python call stacks by time
   * Where sync points (`mx.eval`, `.item()`) are placed

---

### 6.2 Step 2: Idiomatic `mlx.core` refactor

**Goal**
Eliminate obvious Python-side inefficiencies.

**Tasks**

* Scan `src/rag/` and FLUX code for:

  * Python loops over tensor dimensions
  * Frequent `.item()` in training / inference loops
  * Repeated construction of temporary arrays that can be reused
* Refactor:

  * Replace explicit loops with vectorized MLX ops.
  * Minimize conversions between `mx.array` and NumPy / Python lists.
  * Group operations into single expressions where possible to help fusion.

---

### 6.3 Step 3: Benchmarks directory

**Goal**
Create a minimal but meaningful benchmark suite.

**Tasks**

* Add `benchmarks/` directory with:

  * `benchmark_flux_forward_pass.py`
  * `benchmark_rag_query.py`
* Each script:

  * Accepts a small set of CLI flags (batch size, dtype, model variant).
  * Prints clear metrics: average latency, p95, number of iterations, dtype.

Once in place, every optimization attempt gets measured against these baselines.

---

### 6.4 Step 4: Dtype & precision experiments

**Goal**
Quantify the performance vs quality trade-off of `float32` vs `bfloat16`.

**Tasks**

* Add a configuration toggle:

  * CLI flag `--dtype=float32|bfloat16` or env var.
* Run benchmarks:

  * Record latency and memory usage for both dtypes.
  * For FLUX, visually inspect a small sample of outputs for artifacts.
* Decide:

  * Default dtype for interactive usage.
  * Optional “max quality” / “max speed” presets.

---

### 6.5 Step 5: Custom kernel exploration (single target)

**Goal**
Implement **one** fused kernel end-to-end, from profiling to integration.

**Candidate pattern**

* In Flux or RAG:

  * `matmul → bias → activation` sequence that shows up prominently in the profiler.

**Tasks**

1. Identify target block from profiling data.
2. Implement a pure `mlx.core` reference function: `fused_block_ref(x, W, b)`.
3. Measure it with `benchmarks/` microbenchmark.
4. Implement the fused variant via a custom kernel (C++/Metal + Python binding).
5. Compare:

   * Numerical difference vs reference.
   * Latency / throughput difference under benchmarks.

This gives you a **template** for future kernels.

---

### 6.6 Step 6: Continuous monitoring of MLX evolution

**Goal**
Avoid reinventing kernels that MLX later ships natively.

**Tasks**

* Track MLX releases and changelog.
* Maintain a short `docs/mlx-roadmap-notes.md` summarizing:

  * New primitives
  * Fusion improvements
  * Any deprecations affecting your custom extensions

When MLX adds a better primitive:

* Re-evaluate your custom kernel.
* Replace it if the native primitive wins on simplicity and performance.

---

## 7. Outcome & Integration

If you follow the plan above, the repository gains:

* A clear **performance story**: where time is spent, and how MLX is used effectively.
* A **benchmarks/ suite** that makes regressions obvious.
* At least one **real custom kernel** demonstrating the full stack: `mlx.core` graph → C++/Metal op → benchmark.
* Cleaner, idiomatic `mlx.core` usage throughout RAG and FLUX modules.
