# Simulated Traffic
This repository contains a tool for simulating movement trajectories of generated people with their individual occupations, living situations and free time activities. This tool tries to accurately model how people's preferences related to their free time activities and their workplaces dictate their everyday commuting route. Including some randomness, during a weekday, each person drives to work in the morning, spends a variable amount of time there, then goes to one of their chosen free time activities and finally returns home after spending a few hours there depending on the activity.

You can specify the center point of where (in a certain radius) the tool should find residential buildings to populate with generated people living there according to configurable constraints. Then, each person is assigned a workplace. Each potential type of workplace (e.g. restaurants) has their own specified and configurable parameters such as the maximum amount of people working there, for how long people usually stay there during their free time (if applicable) and how the expected working hours are. All of this creates a wide assortment of different routes for each generated day. The routes are simulated as if each person was frequently recording their GPS position along their way, so there is a lot of movement data to work with. These simulated trajectories can be used to test pseudo- or anonymization methods where they can function as a ground-truth.

This program expects that you have set up Openrouteservice as well as OpenPOIservice locally. The simulation can be run either sequentially or in parallel. Example generated outputs are included.
