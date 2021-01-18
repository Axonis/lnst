#! /usr/bin/env python3

from lnst.Recipes.ENRT.SimpleNetworkRecipe import SimpleNetworkRecipe
from lnst.Controller import Controller
from lnst.Controller.RunSummaryFormatter import RunSummaryFormatter
from lnst.Controller.RecipeResults import ResultLevel

import logging

params = {
    "perf_duration": "10",
    "perf_iterations": 1,
    "driver": "ixgbe",
}

ctl = Controller()

recipe = SimpleNetworkRecipe(**params)

ctl.run(recipe)
summary_fmt = RunSummaryFormatter(level=ResultLevel.DEBUG)
for run in recipe.runs:
    logging.debug(summary_fmt.format_run(run))

