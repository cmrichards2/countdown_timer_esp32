import gc

def print_memory_usage():
    """
    Prints the current memory usage and available memory in bytes.
    """
    gc.collect()  # Run garbage collection to free up memory
    used_memory = gc.mem_alloc()  # Memory currently allocated
    free_memory = gc.mem_free()   # Memory available
    total_memory = used_memory + free_memory

    print(f"Total memory: {total_memory} bytes")
    print(f"Used memory: {used_memory} bytes")
    print(f"Free memory: {free_memory} bytes")
  