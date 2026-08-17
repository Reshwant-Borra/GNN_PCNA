"""Figure subsystem: load real Phase-3 / MD data and render publication figures.

No figure in this package invents data. Loaders read the real run manifests and
raise if they are missing; renderers only plot what the loaders return.
"""

__all__ = ["data_loaders", "style", "render", "figure_specs"]
