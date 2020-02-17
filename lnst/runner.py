#! /usr/bin/env python3

from lnst.Recipes.ENRT.OvSBondRecipe import OvSBondRecipe
from lnst.Controller import Controller
from lnst.Controller.RunSummaryFormatter import RunSummaryFormatter
from lnst.Controller.RecipeResults import ResultLevel

import logging

params = {
    "driver": "ixgbe",
    "perf_tests": ("tcp_stream",),
    "ip_versions": ("ipv4",),
    "bonding_mode": "balance-slb",
    "lacp_mode": "active",
    "perf_parallel_streams": 2,
}

ctl = Controller()

recipe = OvSBondRecipe(**params)

ctl.run(recipe)
summary_fmt = RunSummaryFormatter(level=ResultLevel.DEBUG)
for run in recipe.runs:
    logging.debug(summary_fmt.format_run(run))
