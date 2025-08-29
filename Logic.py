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
    Finds the factory that produces a given unit.

    Args:
        unit (Data.Unit): The unit whose producer factory to retrieve.

    Returns:
        (Data.UnitFactory | None): The factory that produces the given unit, or None if no factory is found.
    """

    for block in Data.blocks:
        if isinstance(block, Data.UnitFactory) and unit.name in block.trees.keys():
            return block
    return None

def find_producers_resource(
        resource: Union[str, Data.Resource],
        planet: Union[str, Data.Planet] = 'all') -> list[Data.Block]:
    """
    Retrieve the factories that produce a given resource.

    If no planet is specified, factories from all planets that produce the
    resource are included. If a planet is specified, only factories on that
    planet are returned.

    Args:
        resource (Data.Resource | str): The name of the resource to search for.
        planet (Data.Planet | str, optional): The planet ID to restrict the search to.
            If None, factories from all planets are considered.

    Returns:
        list[Data.Block]: A list of factory blocks capable of producing the resource.
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
        planetEnum = planet if isinstance(planet, Data.Planet) else (
            Data.Planet)[planet.upper()]
        thing = Data.find_resource(resourceName, planetEnum)
        producers.extend(resolve_producer_blocks(thing.producers))

    return producers

def calculate_factory_count(
        factory: Data.Factory,
        outputRate: float,
        outputResource: Optional[str] = None):
    """
    Calculate how many factories are required to produce a resource at a given rate.

    Args:
        factory (Data.Factory): The factory type to calculate for.
        outputRate (float): The desired production rate of the resource.
        outputResource (str | None, optional): The resource to produce, only
            required if the factory outputs more than one type of resource.
            Defaults to None.

    Returns:
        int: The number of factories needed to meet the specified output rate.
    """
    outputs = factory.outputs
    if len(outputs) == 1:
        outputResource = next(iter(outputs)) if outputResource is None else (
            outputResource)
    elif outputResource is None:
        raise ValueError(
            f"Factory {factory.name} has multiple outputs; output resource "
            f"must be specified.")

    if outputResource not in outputs:
        raise ValueError(f"{outputResource} is not produced by {factory.name}.")

    rate_per_factory = outputs[outputResource]
    if Data.find_resource_type(outputResource) == "Fluid":
        return outputRate / rate_per_factory
    else:
        return outputRate * factory.time / (rate_per_factory * 60)


def find_upgrade_path(unit: Data.Unit) -> tuple[list[Union[Data.Unit, None]],
list[Data.UnitFactory]]:
    """
    Determine the upgrade path for a given unit, along with the factories
    required at each step.

    Args:
        unit (Data.Unit): The unit to trace the upgrade path for.

    Returns:
        tuple[list[Data.Unit | None], list[Data.UnitFactory]]:
            A tuple containing two aligned lists:

            - path (list[Data.Unit | None]): The sequence of units in the
              upgrade chain, ordered from highest tier to lowest. The final
              element is always None, marking that the last step does not
              represent a direct 1:1 upgrade.
            - factories (list[Data.UnitFactory]): The factories used for
              each upgrade step. For index i (except the final None),
              factories[i] is the factory that produces path[i].

    Notes:
        The path list will always be one element longer than factories
        because the final None has no corresponding factory.

    Example:
        >>> find_upgrade_path(Data.find_unit("Horizon"))
        (
            [Horizon, Flare, None],
            [Additive Reconstructor, Air Factory]
        )
    """
    path = [unit]
    factories = []
    while path[-1] is not None:
        factories.append(find_producer_unit(path[-1]))
        try:
            path.append(Data.find_unit(factories[-1].trees[path[-1].name]))
        except ValueError:
            break
    return path, factories

def calculate_process_inputs(unit: Data.Unit | str, rate: float) -> dict[str, float]:
    """
    Calculate the cumulative input rates required to produce the first unit in
    path at a given output rate.

    Args:
        unit (Data.Unit | str): Unit to be produced.
        rate (float): Desired production rate of the first unit in path,
            expressed in units per minute.

    Returns:
        dict[str, float]: Mapping of resource names (items, fluids, power) to
        their required input rates, expressed in resources per second.
    """
    if isinstance(unit, str):
        unit = Data.find_unit(unit)

    resources: dict[str, float] = {"power": 0}
    # Pending entries carry their own state
    # (unitName, effectiveRate, ratioSoFar, prevTime)
    pending: list[tuple[str, float, float, float]] = []

    # noinspection PyShadowingNames
    def expand(unit: Data.Unit, rate: float, ratio: float = 1.0, prevTime: float | None = None) -> None:
        path, factories = find_upgrade_path(unit)

        # convert to per-second once at the top of this expansion
        rate /= 60

        for i, u in enumerate(path):
            factory = factories[i]
            t = factory.time if not isinstance(factory.time, dict) else factory.time[u.name]

            if prevTime is not None:
                ratio *= t / prevTime
            prevTime = t

            resources["power"] += factory.power * rate * ratio

            for name, amount in factory.recipes[u.name].items():
                try:
                    resourceType = Data.find_resource_type(name)
                except ValueError:
                    resourceType = None

                rateMulti = 1 if resourceType == "Fluid" else t

                if resourceType is not None:
                    resources[name] = resources.get(name, 0) + amount * ratio * rate / rateMulti
                else:
                    # carry forward state for deeper expansion
                    pending.append((name, amount * ratio * rate / rateMulti, ratio, t))

    # Expand root unit
    expand(unit, rate)

    # Process the dependency tree iteratively
    while pending:
        subName, effRate, ratio, prevTime = pending.pop()
        expand(Data.find_unit(subName), effRate * 60, ratio, prevTime)

    return resources

