"""Physical-needs engine.

Governs the two core survival meters — hunger and hygiene — and the decay
schedules that drain them over real time.  Meeting these needs is necessary
but not sufficient for a healthy avatar; see social_maintenance for the other
half of the equation.

Modules
-------
needs
    Hunger and hygiene meter definitions, current-value tracking, and the
    decay schedule that depletes them when unattended.
actions
    Feed and clean actions: input validation, effect calculation, and meter
    update application.
"""
