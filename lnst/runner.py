#! /usr/bin/env python3

from lnst.Recipes.ENRT.DoubleBondRecipe import DoubleBondRecipe
from lnst.Controller import Controller
from lnst.Controller.RunSummaryFormatter import RunSummaryFormatter
from lnst.Controller.RecipeResults import ResultLevel

import logging

params = {
    "driver": "ixgbe",
    "dev_intr_cpu": 0,
    "perf_tests": ("tcp_stream",),
    "ip_versions": ("ipv4",),
    "perf_tool_cpu": 5,
    "bonding_mode": "802.3ad",
    "miimon_value": 100,
    "xmit_hash_policy": "layer3+4",
}


ctl = Controller()

recipe = DoubleBondRecipe(**params)

ctl.run(recipe)
summary_fmt = RunSummaryFormatter(level=ResultLevel.DEBUG)
for run in recipe.runs:
    logging.debug(summary_fmt.format_run(run))
