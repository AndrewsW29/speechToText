---
source_url: https://kotlinlang.org/docs/coroutines-basics.html
language: kotlin
framework: kotlin
artifact_type: concept
---
Coroutines are lightweight threads managed by the Kotlin runtime. Launch one with launch inside a CoroutineScope and wait for results with async and await. Structured concurrency guarantees that a scope does not finish until all its children complete, which prevents leaked work. Use Dispatchers.IO for blocking input and output and Dispatchers.Default for CPU work.
