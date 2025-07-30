import Data
from typing import Union, Optional

sPriority = {
    0: [
        'Scrap',
        'Water'
    ],
    1: [
        'Slag',
        'Spore pod'
    ],
    2: [
        'Copper',
        'Lead',
        'Oil',
        'Sand',
        'Titanium',
        'Thorium'
    ],
    3: [
        'Metaglass',
        'Graphite',
        'Coal',
        'Plastanium',
        'Phase fabric',
        'Cryofluid'
    ],
    4: [
        'Silicon',
        'Pyratite'
    ],
    5: [
        'Surge alloy',
        'Blast compound'
    ]}

ePriority = {
    0: [
        'Sand',
        'Graphite',
        'Beryllium',
        'Water'
    ],
    1: [
        'Hydrogen',
        'Ozone',
        'Silicon',
        'Heat'
    ],
    2: [
        'Slag',
        'Oxide',
        'Tungsten',
        'Nitrogen',
        'Cyanogen',
        'Arkycite'
    ],
    3: [
        'Surge alloy',
        'Thorium',
        'Carbide'
    ],
    4: [
        'Phase fabric'
    ],
    5: [
        'Neoplasm'
    ]
}

class Recursion:
    def __init__(self, unresolvedInputs: dict[str, float]):
        self.unresolvedInputs: dict = unresolvedInputs

    @staticmethod
    def calculate_inputs(block: str, outputRate: float, outputResource: str) -> dict[str, float]:
        blockData = Data.find_block(block)
        if outputResource in blockData.outputs.keys():
            count = outputRate / blockData.outputs[outputResource]
            inputs = blockData.inputs
            inputRates = {}
            for key, value in inputs.items():
                inputRates[key] = count * value
            return inputRates
        raise IOError(f'{outputResource} not produced by {blockData.name}.')

    def resolve_input(self, rInput: str, block: str):
        if rInput in self.unresolvedInputs.keys():
            self.calculate_inputs(block, self.unresolvedInputs[rInput], rInput)
        else:
            raise IOError(f'{rInput} not in list of resources awaiting production lines.')

def find_producer_unit(unit: Data.Unit) -> Union[Data.UnitFactory, None]:
    """
    :param unit: Unit object to find the producing block for.
    :return: Block object that produces the input unit.
    """

    for block in Data.blocks:
        if isinstance(block, Data.UnitFactory) and unit.name in block.trees.keys():
            return block
    return None

def find_producers_resource(
        resource: Union[str, Data.Resource],
        planet: Union[str, Data.Planet] = 'all') -> list[Data.Block]:
    """
    :param resource: Input resource
    :param planet: Optional specifier, used mainly for resources found on multiple planets
    :return: List of Block objects that produce the input resource. If planet is specified, limits blocks found to only that planet.
    """
    resourceName = resource if isinstance(resource, str) else resource.name
    producers = []

    def resolve_producer_blocks(names):
        return [b for b in Data.blocks if b.name in names]

    if planet == 'all' or planet == 'Mixtech':
        for thing in Data.resources:
            if thing.name == resourceName:
                producers.extend(resolve_producer_blocks(thing.producers))
    else:
        planetEnum = planet if isinstance(planet, Data.Planet) else Data.Planet[planet.upper()]
        thing = Data.find_resource(resourceName, planetEnum)
        producers.extend(resolve_producer_blocks(thing.producers))

    return producers

def calculate_factory_count(
        factory: Data.Factory,
        outputRate: float,
        outputResource: Optional[str] = None):
    """

    :param factory:
    :param outputRate:
    :param outputResource:
    :return:
    """
    outputs = factory.outputs
    if len(outputs) == 1:
        outputResource = next(iter(outputs)) if outputResource is None else outputResource
    elif outputResource is None:
        raise ValueError(
            f"Factory {factory.name} has multiple outputs; output resource must be specified.")

    if outputResource not in outputs:
        raise ValueError(f"{outputResource} is not produced by {factory.name}.")

    rate_per_factory = outputs[outputResource]
    if Data.find_resource_type(outputResource) == "Fluid":
        return outputRate / rate_per_factory
    else:
        return outputRate * factory.time / (rate_per_factory * 60)


# noinspection PyBroadException
def find_upgrade_path(unit: Data.Unit):
    """
    Finds upgrade path to input unit.
    :param unit:
    :return:
    """
    path = [unit]
    factories = []
    while path[-1] is not None:
        factories.append(find_producer_unit(path[-1]))
        try:
            path.append(Data.find_unit(factories[-1].trees[path[-1].name]))
        except Exception:
            break
    return path, factories

def calculate_process_inputs(path, factories, rate):
    """
    Calculates the inputs for the entire unit production process, start to finish.
    :param path:
    :param factories:
    :param rate:
    :return:
    """
    # factory.recipes[path[factory.index()].name] finds output unit inputs dir
    resources = {}
    for factory in factories:
        # for resource, amount in factory.recipes[path[factory.index()].name].items():
        #     if resource not in resources:
        #         try:
        #             if Data.find_resource_type(resource) == 'Item':
        #                 resources[resource] = amount * rate / (60 * factory.time)
        #             elif Data.find_resource_type(resource) == 'Fluid':
        #                 resources[resource] = amount
        #         except:
        #             resources[resource] = amount
        if path[factory.index()].name in resources.keys():
            countMulti = factory.recipes[path[factory.index()].name]
        else:
            countMulti = 1


# resource is items/recipe, recipe time in seconds, rate in units/min (final output)
