"""Multi-robot task allocation."""

from swarmforge.allocation.allocation_manager import AllocationManager, make_allocator
from swarmforge.allocation.auction import AuctionAllocator
from swarmforge.allocation.base import AllocationResult, CostMatrix
from swarmforge.allocation.greedy import GreedyAllocator
from swarmforge.allocation.hungarian import HungarianAllocator, solve_rectangular

__all__ = ["AllocationManager", "AllocationResult", "AuctionAllocator", "CostMatrix", "GreedyAllocator",
           "HungarianAllocator", "make_allocator", "solve_rectangular"]
