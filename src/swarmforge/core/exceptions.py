"""Exception hierarchy."""


class SwarmForgeError(Exception):
    """Base class for all SwarmForge errors."""


class ConfigError(SwarmForgeError):
    """Invalid or inconsistent configuration."""


class ValidationError(SwarmForgeError):
    """Invalid domain object or illegal state transition."""


class AllocationError(SwarmForgeError):
    """Invalid allocation result or infeasible allocation request."""


class PlanningError(SwarmForgeError):
    """Path planning failure that callers are expected to handle."""


class InvariantViolation(SwarmForgeError):
    """A simulation safety invariant was violated."""
