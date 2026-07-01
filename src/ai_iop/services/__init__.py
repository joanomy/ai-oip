"""Services: business logic that coordinates repositories, agents,
and collectors to accomplish a unit of work.

This is the layer allowed to know about both persistence (repositories)
and AI execution (agents) — neither of those layers know about each other.

Dependency rule: depends on repositories, agents, collectors, core.
"""
