# -*- coding: utf-8 -*-
#
# Copyright (c) 2020, CloudBlue
# All rights reserved.
#

async def generate(client, parameters, progress_callback, renderer_type, extra_context_callback):
    yield [1]
    yield [2]
    progress_callback(10, 10)
