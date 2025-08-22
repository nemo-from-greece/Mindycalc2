from enum import Enum
from typing import List, Optional, Tuple, Dict, Union
from PIL import Image
import customtkinter as ctk

class Planet(Enum):
    SERPULO = 0
    EREKIR = 1

class Resource:
    """
    Base class for any resource (item or fluid).

    Attributes:
        name (str): Name of the resource.
        planet (int): Planet ID.
        allBlocks (List[Block]): List of all blocks in the game.
        producers (List[Block]): Initial list of blocks that produce this resource.
        image (str): File path to the image representing the resource.
    """

    def __init__(
        self,
        name: str,
        planet: int,
        allBlocks: List['Block'],
        producers: List[str],
        image: str
    ):
        self.name: str = name
        self.planet: Planet = Planet(planet)
        self.allBlocks: List['Block'] = allBlocks
        self.producers: List[str] = producers.copy()
        self.image: str = image

class Item(Resource):
    def __init__(
        self,
        name: str,
        planet: int,
        allBlocks: List['Block'],
        producers: List[str],
        image: str,
        isOre: bool,
        allDrills: bool = False
    ):
        """
        Represents an item, optionally mined as an ore.

        Args:
            isOre (bool): True if the item is mined.
            allDrills (bool): Only applicable to ores. Can all drills on the same planet as this ore mine it?
        """
        super().__init__(name, planet, allBlocks, producers, image)
        self.isOre: bool = isOre

        if isOre and allDrills:
            self.producers.extend(
                b.name for b in allBlocks if isinstance(b, Drill) and b.planet == self.planet
            )

class Fluid(Resource):
    def __init__(
        self,
        name: str,
        planet: int,
        allBlocks: List['Block'],
        producers: List[str],
        image: str,
        isGas: bool,
        allPumps: bool
    ):
        """
        Represents a fluid resource, optionally a gas.

        Args:
            isGas (bool): True if the fluid is a gas.
            allPumps (bool): Can all pumps on the same planet as this fluid pump it?
        """
        super().__init__(name, planet, allBlocks, producers, image)
        self.isGas: bool = isGas

        if allPumps:
            self.producers.extend(
                b.name for b in allBlocks if isinstance(b, Pump) and b.planet == self.planet
            )

class Unit:
    def __init__(
            self,
            name: str,
            planet: int,
            image: str
    ):
        """
        Represents a unit.

        Args:
            name (str): Unit name.
            planet (int): Planet ID.
            image (str): Path to the image file of the unit.
        """
        self.name: str = name
        self.planet: Planet = Planet(planet)
        self.image: str = image

class Block:
    def __init__(
            self,
            name: str,
            planet: int,
            power: int, image: str
    ):
        """
        Base class for all blocks.

        Args:
            name (str): Block name.
            planet (int): Planet ID.
            power (int): Power consumed or produced.
            image (str): File path to image.
        """
        self.name: str = name
        self.planet: Planet = Planet(planet)
        self.power: int = power
        self.image: str = image

class Pump(Block):
    def __init__(
        self,
        name: str,
        planet: int,
        image: str,
        pSpeed: int,
        power: int = 0,
        inputs: Dict[str, float] = None
    ):
        """
        A block that pumps fluids from sources.

        Args:
            pSpeed (int): Pump speed under full coverage.
            power (int): Power consumption.
            inputs (Dict[int, float]): Non-power inputs required for pump operation, name,
            and input rate.
        """
        super().__init__(name, planet, power, image)
        self.pSpeed: int = pSpeed
        self.inputs: dict[str, float] = inputs

class Turret(Block):
    # noinspection PyShadowingNames
    def __init__(
        self,
        name: str,
        planet: int,
        image: str,
        reloadTime: int,
        burst: int,
        intraBurstDelay: int = 0,
        isFluidAmmo: bool = False,
        coolant: Optional[Dict[str, Tuple[float, float]]] = None,
        fluids: Optional[Dict[str, float]] = None,
        ammo: Optional[Dict[str, Union[int, Tuple[float, int]]]] = None,
        ammoUse: int = 1,
        power: int = 0,
        consumeAmmoOnce: bool = True,
        heatScaling: Optional[Tuple[float, str]] = None
    ):
        """
        Represents a turret that consumes either item or fluid ammo, with support
        for burst fire, coolant, and ammo consumption variations.

        Args:
            name (str): Name of the turret.
            planet (int): Planet ID the turret belongs to.
            image (str): File path to the turret image.
            reloadTime (int): Time in frames between bursts.
            intraBurstDelay (int): Delay between shots in a burst, in frames.
            burst (int): Number of bullets fired in one burst.
            isFluidAmmo (bool): True if the turret uses fluid-based ammo.
            coolant (Optional[Dict]): Coolant data {coolant: (fire rate multi, ammo multi)}.
            fluids (Optional[Dict]): Fluid consumption data {fluid: consumption rate}.
            ammo (Optional[Dict]): Ammo data {ammo type: (rate multiplier, ammo per item)}.
            ammoUse (int): Ammo used per firing event (burst or per shot).
            power (int): Power consumption, if any.
            consumeAmmoOnce (bool): Whether ammo is consumed once per burst (True) or per bullet (False).
            heatScaling (Optional[Tuple[float, str]]): Reload speed multiplier at max heat, relation between heat and reload multiplier otherwise.
        """
        super().__init__(name, planet, power, image)
        self.reloadTime = reloadTime
        self.intraBurstDelay = intraBurstDelay
        self.burst = burst
        self.isFluidAmmo = isFluidAmmo
        self.coolant = coolant if not isFluidAmmo else None
        self.fluids = fluids if not isFluidAmmo else {}
        self.ammo = ammo or {}
        self.ammoUse = ammoUse
        self.consumeAmmoOnce = consumeAmmoOnce
        self.heatScaling = heatScaling

    def fire_rate(
        self,
        bullet: Optional[str] = None,
        coolant: Optional[str] = None,
        heat: Optional[float] = 0
    ) -> float:
        """
        Calculates the rate of ammo consumption (items/second) for continuous firing.

        Args:
            bullet (str): The ammo type key (ignored for fluid or heat-only turrets).
            coolant (Optional[str]): Coolant used, if any.
            heat (Optional[float]): Heat input for turrets using heat-based scaling.

        Returns:
            float: Items consumed per second (or 1/shot time for heat-only turrets).
        """
        effectiveReload = self.reloadTime

        # Apply heat multiplier if scaling is defined
        if self.heatScaling and heat:
            maxMult, expr = self.heatScaling
            try:
                multiplier = eval(expr, {'heat': heat})
                multiplier = min(float(multiplier), maxMult)
                effectiveReload /= multiplier
            except Exception as e:
                raise ValueError(f"Invalid heat expression '{expr}': {e}")

        # Apply coolant multiplier (ignored if heatScaling is present)
        elif coolant and self.coolant and coolant in self.coolant:
            coolantInfo = self.coolant[coolant]
            effectiveReload /= coolantInfo[1]

        burstTime = effectiveReload + self.intraBurstDelay * (self.burst - 1)
        burstTimeSeconds = burstTime / 60

        if not self.isFluidAmmo and not self.heatScaling:
            rateMult, ammoPer = self.ammo[bullet]
            used_ammo = self.ammoUse if self.consumeAmmoOnce else self.ammoUse * self.burst
            return (used_ammo * rateMult) / (burstTimeSeconds * ammoPer)
        else:
            return 1.0 / burstTimeSeconds

class Generator(Block):
    def __init__(
        self,
        name: str,
        planet: int,
        image: str,
        multiRecipes: bool,
        inputs: Union[Dict[str, int], List[Dict[str, int]]],
        outputs: Union[Dict[str, int], List[Dict[str, int]]],
        prodTime: int,
        powerIn: int = 0
    ):
        """
        Represents a generator block that consumes input resources to produce power.

        Args:
            name (str): Name of the generator.
            planet (int): Planet ID.
            image (str): File path to the image used for the generator.
            multiRecipes (bool): True if the generator has multiple production recipes.
            inputs (dict or list of dict): If multiRecipes is False, a single recipe as {resource: amount}.
                                           If True, a list of such dictionaries for each recipe.
            outputs (dict or list of dict): Same structure as `inputs`, representing products.
            prodTime (int): Production time per recipe in frames (1 second = 60 frames).
            powerIn (int, optional): Power consumed by the generator (default is 0).
        """
        super().__init__(name, planet, powerIn, image)
        self.multiRecipes: bool = multiRecipes
        self.inputs: Union[Dict[str, int], List[Dict[str, int]]] = inputs
        self.outputs: Union[Dict[str, int], List[Dict[str, int]]] = outputs
        self.prodTime: int = prodTime

class Factory(Block):
    def __init__(
        self,
        name: str,
        planet: int,
        power: int,
        image: str,
        inputs: Dict[str, float],
        outputs: Dict[str, float],
        time: int,
        heatScaling: Optional[Tuple[float, str]] = None
    ):
        """
        A factory that processes inputs into outputs.

        Args:
            inputs (Dict[str, float]): Ingredients required.
            outputs (Dict[str, float]): Products created.
            time (int): Time to complete one recipe in frames (60 fps).
            heatScaling (Optional[Tuple[float, str]]): Optional speed-up rule, e.g. (2.0, 'heat / 10')
        """
        super().__init__(name, planet, power, image)
        self.inputs = inputs
        self.outputs = outputs
        self.time = time
        self.heatScaling = heatScaling

    def output_rate(self, heat: float = 0) -> Dict[str, Dict[str, float]]:
        """
        Computes output production rates in items/second.

        Args:
            heat (Optional[float]): Heat applied to factory.

        Returns:
            Dict[str, Dict[str, float]]: {Inputs: {Resource: rate}, Outputs: {Resource: rate}}
        """

        def scale_recipe(recipe: dict, mult: float, effTime: float) -> dict:
            scaledRecipe = {}
            for key, value in recipe.items():
                if (find_resource(key, self.planet) is Fluid or find_resource(key, self.planet) == 'heat' or
                        find_resource(key, self.planet) == 'power'):
                    scaledRecipe[key] = value * mult
                else:
                    scaledRecipe[key] = 60 * value / effTime
            return scaledRecipe

        effectiveTime = self.time
        multiplier = 1

        if self.heatScaling and heat:
            maxMult, expr = self.heatScaling
            try:
                multiplier = eval(expr, {'heat': heat})
                multiplier = min(float(multiplier), maxMult)
                effectiveTime /= multiplier
            except Exception as e:
                raise ValueError(f"Invalid heat expression '{expr}': {e}")

        scaledInputs = scale_recipe(self.inputs, multiplier, effectiveTime)
        scaledOutputs = scale_recipe(self.outputs, multiplier, effectiveTime)

        return {'Inputs': scaledInputs, 'Outputs': scaledOutputs}

class Drill(Factory):
    def __init__(
        self,
        name: str,
        planet: int,
        power: int,
        image: str,
        inputs: Dict[str, float],
        drillables: Dict[str, float],
        coolant: Optional[Tuple[str, float, float]] = None,
    ):
        """
        A block that drills ores from the ground.

        Args:
            drillables (Dict[str, float]): Extraction speeds of drillables at full coverage.
            coolant (Optional[Tuple[str, float, float]]): Coolant name, feed rate, and boost multiplier.
            power (int): Power consumption.
        """
        super().__init__(name, planet, power, image, inputs, drillables, 60)
        self.coolant: Optional[Tuple[str, float, float]] = coolant

class UnitFactory(Block):
    def __init__(
        self,
        name: str,
        planet: int,
        power: int,
        image: str,
        trees: Union[Dict[str, str], Dict[str, None]],
        recipes: Dict[str, Dict[str, int]],
        time: Union[int, Dict[str, float]]
    ):
        """
        A factory that produces units from other units and resources.

        Args:
            name (str): Name of the block.
            planet (int): Planet ID.
            power (int): Power consumption.
            image (str): Path to the image file of the block.
            trees (Union[Dict[str, str], Dict[str, None]]): Maps output unit names to input unit
            names. None if the unit is T1.
            recipes (Dict[str, Dict[str, int]]): Maps output unit names to required input resources.
            time (Union[int, Dict[str, float]]): Build time for units.
                - If all units take the same time, provide a single int (in seconds).
                - If build times vary, provide a dict mapping unit names to build time in seconds.
        """
        super().__init__(name, planet, power, image)
        self.trees: Union[Dict[str, str], Dict[str, None]] = trees
        self.recipes: Dict[str, Dict[str, int]] = recipes
        self.time: Union[int, Dict[str, float]] = time

def find_resource(name, planet):
    for i, resource in enumerate(resources):
        if resource.name == name and resource.planet == planet:
            return resources[i]
    raise ValueError(f"Resource '{name}' not found")

def find_resource_type(name):
    for i in resources:
        if i.name == name:
            if isinstance(i, Item):
                return "Item"
            else:
                return "Fluid"
    raise ValueError(f"Resource '{name}' not found")

def find_block(name):
    for i, block in enumerate(blocks):
        if block.name == name:
            return blocks[i]
    raise ValueError(f"Block '{name}' not found")

def find_unit(name):
    for i, unit in enumerate(units):
        if unit.name == name:
            return units[i]
    raise ValueError(f"Unit '{name}' not found")

def load_image(location):
    return ctk.CTkImage(Image.open(location).convert('RGBA'), size=(32, 32))

# def list_coolants():
#     coolants = []
#     for i in blocks:
#         if isinstance(i, Turret) and i.coolant:
#             for key in i.coolant:
#                 if key not in coolants:
#                     coolants.append(key)
#     return coolants

blocks = [
    Turret('Duo',
           0,
           'Images/Blocks/Turrets/Duo.png',
           20,
           1,
           coolant={'Water': (6.0, 1.2), 'Cryofluid': (6.0, 1.45)},
           ammo={'Copper': (1.0, 2), 'Graphite': (0.6, 4), 'Silicon': (1.5, 5)}), # Duo
    Turret('Scatter', 0, 'Images/Blocks/Turrets/Scatter.png',
           18,
           2,
           5,
           coolant={'Water': (12.0, 1.4), 'Cryofluid': (12.0, 1.9)},
           ammo={'Scrap': (0.5, 5), 'Lead': (1.0, 4), 'Metaglass': (0.8, 5)}), # Scatter
    Turret('Scorch',
           0,
           'Images/Blocks/Turrets/Scorch.png',
           6,
           1,
           coolant={'Water': (6.0, 1.06), 'Cryofluid': (6.0, 1.135)},
           ammo={'Coal': (1.0, 3), 'Pyratite': (1.0, 6)}), # Scorch
    Turret('Hail',
           0,
           'Images/Blocks/Turrets/Hail.png',
           60,
           1,
           coolant={'Water': (6.0, 1.2), 'Cryofluid': (6.0, 1.45)},
           ammo={'Graphite': (1.0, 2), 'Silicon': (1.2, 3), 'Pyratite': (1.0, 4)}), # Hail
    Turret('Wave',
           0,
           'Images/Blocks/Turrets/Wave.png',
           3,
           1,
           0,
           True,
           None,
           {'Water': 20, 'Cryofluid': 20, 'Slag': 20, 'Oil': 20}), # Wave
    Turret('Arc',
           0,
           'Images/Blocks/Turrets/Arc.png',
           35,
           1,
           coolant={'Water': (6.0, 1.2), 'Cryofluid': (6.0, 1.45)},
           power=198), # Arc
    Turret('Lancer',
           0,
           'Images/Blocks/Turrets/Lancer.png',
           80,
           1,
           coolant={'Water': (12.0, 1.4), 'Cryofluid': (12.0, 1.9)},
           power=360), # Lancer
    Turret('Parallax',
           0,
           'Images/Blocks/Turrets/Parallax.png',
           0,
           1,
           power=198), # Parallax
    Turret('Swarmer',
           0,
           'Images/Blocks/Turrets/Swarmer.png',
           30,
           4,
           5,
           coolant={'Water': (18.0, 1.6), 'Cryofluid': (18.0, 2.35)},
           ammo={'Blast compound': (1.0, 5), 'Pyratite': (1.0, 5), 'Surge alloy': (1.0, 4)},
           consumeAmmoOnce=False), # Swarmer
    Turret('Salvo',
           0,
           'Images/Blocks/Turrets/Salvo.png',
           31,
           4,
           3,
           coolant={'Water': (12.0, 1.4), 'Cryofluid': (12.0, 1.9)},
           ammo={'Copper': (1.0, 2), 'Graphite': (0.6, 4), 'Pyratite': (1.0, 5), 'Silicon': (1.5, 5), 'Thorium': (1.0, 4)},
           consumeAmmoOnce=False), # Salvo
    Turret('Segment',
           0,
           'Images/Blocks/Turrets/Segment.png',
           8,
           1,
           power=480), # Segment
    Turret('Tsunami',
           0,
           'Images/Blocks/Turrets/Tsunami.png',
           3,
           2,
           isFluidAmmo=True,
           ammo={'Water': 50, 'Cryofluid': 50, 'Slag': 50, 'Oil': 50}), # Tsunami
    Turret('Fuse',
           0,
           'Images/Blocks/Turrets/Fuse.png',
           35,
           3,
           coolant={'Water': (18.0, 1.6), 'Cryofluid': (18.0, 2.35)},
           ammo={'Titanium': (1.3, 4), 'Thorium': (1.0, 5)}), # Fuse
    Turret('Ripple',
           0,
           'Images/Blocks/Turrets/Ripple.png',
           60,
           4,
           coolant={'Water': (18.0, 1.6), 'Cryofluid': (18.0, 2.35)},
           ammo={'Graphite': (1.0, 2), 'Silicon': (1.2, 3), 'Pyratite': (1.0, 4), 'Blast compound': (1.0, 4), 'Plastanium': (1.0, 2)}), # Ripple
    Turret('Cyclone',
           0,
           'Images/Blocks/Turrets/Cyclone.png',
           8,
           1,
           coolant={'Water': (18.0, 1.6), 'Cryofluid': (18.0, 2.35)},
           ammo={'Metaglass': (0.8, 2), 'Blast compound': (1.0, 5), 'Plastanium': (1.0, 4), 'Surge alloy': (1.0, 5)}), # Cyclone
    Turret('Foreshadow',
           0,
           'Images/Blocks/Turrets/Foreshadow.png',
           200,
           1,
           coolant={'Water': (60.0, 1.16), 'Cryofluid': (60.0, 1.36)},
           ammo={'Surge Alloy': (1.0, 1)},
           ammoUse=5,
           power=600), # Foreshadow
    Turret('Spectre',
           0,
           'Images/Blocks/Turrets/Spectre.png',
           7,
           1,
           coolant={'Water': (60.0, 1.2), 'Cryofluid': (60.0, 1.45)},
           ammo={'Graphite': (1.7, 4), 'Thorium': (1.0, 2), 'Pyratite': (1.0, 3)}), # Spectre
    Turret('Meltdown',
           0,
           'Images/Blocks/Turrets/Meltdown.png',
           90,
           1,
           coolant={'Water': (30.0, 1.0), 'Cryofluid': (30.0, 2.25)},
           power=1020), # Meltdown
    Turret('Breach',
           1,
           'Images/Blocks/Turrets/Breach.png',
           40,
           1,
           coolant={'Water': (15.0, 2.5)},
           ammo={'Beryllium': (1, 1), 'Tungsten': (1, 1), 'Carbide': (0.2, 2)},
           ammoUse=2), # Breach
    Turret('Diffuse',
           1,
           'Images/Blocks/Turrets/Diffuse.png',
           30,
           15,
           coolant={'Water': (15.0, 2.5)},
           ammo={'Graphite': (1, 1), 'Silicon': (1, 1), 'Oxide': (1, 2)},
           ammoUse=3), # Diffuse
    Turret('Sublimate',
           1,
           'Images/Blocks/Turrets/Sublimate.png',
           0,
           1,
           0,
           True,
           None,
           {'Ozone': 15, 'Cyanogen': 10}), # Sublimate
    Turret('Titan',
           1,
           'Images/Blocks/Turrets/Titan.png',
           138,
           1,
           coolant={'Water': (30, 1.3)},
           fluids={'Hydrogen': 5},
           ammo={'Thorium': (1, 1), 'Oxide': (0.65, 1), 'Carbide': (0.8, 1)},
           ammoUse=4), # Titan
    Turret('Disperse',
           1,
           'Images/Blocks/Turrets/Disperse.png',
           9,
           4,
           coolant={'Water': (20, 1.8333)},
           ammo={'Tungsten': (1, 3), 'Thorium': (0.85, 1), 'Silicon': (1, 4), 'Surge alloy': (0.75, 3)}), # Disperse
    Turret('Afflict',
           1,
           'Images/Blocks/Turrets/Afflict.png',
           100,
           1,
           power=300,
           heatScaling=(2.0, 'heat / 10')), # Afflict
    Turret('Lustre',
           1,
           'Images/Blocks/Turrets/Lustre.png',
           0,
           1,
           0,
           True,
           None,
           ammo={'Nitrogen': 6},
           power=1), # Lustre
    Turret('Scathe',
           1,
           'Images/Blocks/Turrets/Scathe.png',
           600,
           1,
           coolant={'Water': (15, 2.5)},
           ammo={'Carbide': (1, 1), 'Phase fabric': (0.8, 3), 'Surge alloy': (0.9, 1)},
           ammoUse=15), # Scathe
    Turret('Smite',
           1,
           'Images/Blocks/Turrets/Smite.png',
           100,
           10,
           coolant={'Water': (15, 2.5)},
           ammo={'Surge alloy': (1, 1)},
           ammoUse=2), # Smite
    Turret('Malign',
           1,
           'Images/Blocks/Turrets/Malign.png',
           7,
           1,
           power=2400,
           heatScaling=(2.0, 'heat / 72')), # Malign
    Pump('Mechanical pump',
         0,
         'Images/Blocks/Extractors/Mechanical Pump.png',
         7), # Mechanical Pump
    Pump('Rotary pump',
         0,
         'Images/Blocks/Extractors/Rotary Pump.png',
         48,
         18), # Rotary Pump
    Pump('Impulse pump',
         0,
         'Images/Blocks/Extractors/Impulse Pump.png',
         118,
         78), # Impulse Pump
    Pump('Reinforced Pump',
         1,
         'Images/Blocks/Extractors/Reinforced Pump.png',
         80,
         inputs={'Hydrogen': 1.5}), # Reinforced Pump
    Factory('Graphite Press',
            0,
            0,
            'Images/Blocks/Item production/Graphite Press.png',
            {'Coal': 2},
            {'Graphite': 1},
            90), # Graphite Press
    Factory('Multi-Press',
            0,
            108,
            'Images/Blocks/Item production/Multi-Press.png',
            {'Coal': 3, 'Water': 6},
            {'Graphite': 2},
            30), # Multi-Press
    Factory('Silicon Smelter',
            0,
            30,
            'Images/Blocks/Item production/Silicon Smelter.png',
            {'Coal': 2, 'Sand': 1},
            {'Silicon': 1},
            40), # Silicon Smelter
    Factory('Silicon Crucible',
            0,
            240,
            'Images/Blocks/Item production/Silicon Crucible.png',
            {'Coal': 6, 'Sand': 4, 'Pyratite': 1},
            {'Silicon': 8},
            90), # Silicon Crucible
    Factory('Kiln',
            0,
            36,
            'Images/Blocks/Item production/Kiln.png',
            {'Lead': 1, 'Sand': 1},
            {'Metaglass': 1},
            30), # Kiln
    Factory('Plastanium Compressor',
            0,
            180,
            'Images/Blocks/Item production/Plastanium Compressor.png',
            {'Titanium': 2, 'Oil': 15},
            {'Plastanium': 1},
            60), # Plastanium Compressor
    Factory('Phase Weaver',
            0,
            300,
            'Images/Blocks/Item production/Phase Weaver.png',
            {'Sand': 10, 'Thorium': 4},
            {'Phase fabric': 1},
            120), # Phase Weaver
    Factory('Surge Smelter',
            0,
            240,
            'Images/Blocks/Item production/Surge Smelter.png',
            {'Copper': 3, 'Lead': 4, 'Titanium': 2, 'Silicon': 3},
            {'Surge alloy': 1},
            75), # Surge Smelter
    Factory('Cryofluid Mixer',
            0,
            60,
            'Images/Blocks/Item production/Cryofluid Mixer.png',
            {'Titanium': 1, 'Water': 12},
            {'Cryofluid': 12},
            120), # Cryofluid Mixer
    Factory('Pyratite Mixer',
            0,
            12,
            'Images/Blocks/Item production/Pyratite Mixer.png',
            {'Sand': 2, 'Coal': 1, 'Lead': 2},
            {'Pyratite': 1},
            80), # Pyratite Mixer
    Factory('Blast Mixer',
            0,
            24,
            'Images/Blocks/Item production/Blast Mixer.png',
            {'Pyratite': 1, 'Spore Pod': 1},
            {'Blast compound': 1},
            80), # Blast Mixer
    Factory('Melter',
            0,
            60,
            'Images/Blocks/Item production/Melter.png',
            {'Scarp': 1},
            {'Slag': 12},
            10), # Melter
    Factory('Separator',
            0,
            60,
            'Images/Blocks/Item production/Separator.png',
            {'Slag': 4},
            {'Copper': 5/12, 'Lead': 1/4, 'Graphite': 1/6, 'Titanium': 1/6},
            35), # Separator
    Factory('Disassembler',
            0,
            240,
            'Images/Blocks/Item production/Disassembler.png',
            {'Slag': 7.2, 'Scrap': 1},
            {'Graphite': 0.2, 'Sand': 0.4, 'Titanium': 0.2, 'Thorium': 0.2},
            30), # Disassembler
    Factory('Spore Press',
            0,
            42,
            'Images/Blocks/Item production/Spore Press.png',
            {'Spore pod': 1},
            {'Oil': 18},
            20), # Spore Press
    Factory('Pulverizer',
            0,
            30,
            'Images/Blocks/Item production/Pulverizer.png',
            {'Scrap': 1},
            {'Sand': 1},
            40), # Pulverizer
    Factory('Coal Centrifuge',
            0,
            42,
            'Images/Blocks/Item production/Coal Centrifuge.png',
            {'Oil': 6},
            {'Coal': 1},
            30), # Coal Centrifuge
    Factory('Silicon Arc Furnace',
            1,
            300,
            'Images/Blocks/Item production/Silicon Arc Furnace.png',
            {'Sand': 4, 'Graphite': 1},
            {'Silicon': 4},
            50), # Silicon Arc Furnace
    Factory('Electrolyzer',
            1,
            60,
            'Images/Blocks/Item production/Electrolyzer.png',
            {'Water': 10},
            {'Hydrogen': 6, 'Ozone': 4},
            10), # Electrolyzer
    Factory('Atmospheric Concentrator',
            1,
            120,
            'Images/Blocks/Item production/Atmospheric Concentrator.png',
            {'Heat': 6},
            {'Nitrogen': 4},
            80), # Atmospheric Concentrator
    Factory('Oxidation Chamber',
            1,
            30,
            'Images/Blocks/Item production/Oxidation Chamber.png',
            {'Beryllium': 1, 'Ozone': 5},
            {'Oxide': 1, 'Heat':5},
            120), # Oxidation Chamber
    Factory('Electric Heater',
            0,
            100,
            'Images/Blocks/Item production/Electric Heater.png',
            {},
            {'Heat': 3},
            60), # Electric Heater
    Factory('Slag Heater',
            1,
            0,
            'Images/Blocks/Item production/Slag Heater.png',
            {'Slag': 40},
            {'Heat': 8},
            60), # Slag Heater
    Factory('Phase Heater',
            1,
            0,
            'Images/Blocks/Item production/Phase Heater.png',
            {'Phase fabric': 1},
            {'Heat': 15},
            960), # Phase Heater
    Factory('Carbide Crucible',
            1,
            120,
            'Images/Blocks/Item production/Carbide Crucible.png',
            {'Graphite': 3, 'Tungsten': 2, 'Heat': 10},
            {'Carbide': 1},
            135,
            (4, 'heat/10')), # Carbide Crucible
    Factory('Surge Crucible',
            1,
            90,
            'Images/Blocks/Item production/Surge Crucible.png',
            {'Scrap': 40, 'Silicon': 1, 'Heat': 10},
            {'Surge alloy': 1},
            180,
            (4, 'heat/10')), # Surge Crucible
    Factory('Phase Synthesizer',
            1,
            480,
            'Images/Blocks/Item production/Phase Synthesizer.png',
            {'Sand': 6, 'Thorium': 2, 'Ozone': 2, 'Heat': 8},
            {'Phase fabric': 1},
            120,
            (4, 'heat/8')), # Phase Synthesizer
    Generator('Combustion Generator',
              0,
              'Images/Blocks/Generators/Combustion Generator.png',
              True,
              [{'Coal': 1}, {'Spore pod': 1}, {'Pyratite': 1}, {'Blast compound': 1}],
              [{'Power': 60}, {'Power': 60*1.15}, {'Power': 60*1.4}, {'Power': 60*0.4}],
              120), # Combustion Generator
    Generator('Steam Generator',
              0,
              'Images/Blocks/Generators/Steam Generator.png',
              True,
              [{'Coal': 1, 'Water': 6}, {'Spore pod': 1, 'Water': 6}, {'Pyratite': 1, 'Water': 6}, {'Blast compound': 1, 'Water': 6}],
              [{'Power': 330}, {'Power': 330*1.15}, {'Power': 330*1.4}, {'Power': 330*0.4}],
              90), # Steam Generator
    Generator('Differential Generator',
              0,
              'Images/Blocks/Generators/Differential Generator.png',
              False,
              {'Pyratite': 1, 'Cryofluid': 6},
              {'Power': 1080},
              220), # Differential Generator
    Generator('RTG Generator',
              0,
              'Images/Blocks/Generators/RTG Generator.png',
              True,
              [{'Thorium': 1}, {'Phase fabric': 1}],
              [{'Power': 270}, {'Power': 270*0.6}],
              14*60), # RTG Generator
    Generator('Thorium Reactor',
              0,
              'Images/Blocks/Generators/Thorium Reactor.png',
              False,
              {'Thorium': 1, 'Cryofluid': 2.4},
              {'Power': 900},
              360), # Thorium Reactor
    Generator('Impact Reactor',
              0,
              'Images/Blocks/Generators/Impact Reactor.png',
              False,
              {'Blast compound': 1, 'Cryofluid': 15, 'Power': 1500},
              {'Power': 7800},
              140), # Impact Reactor
    Generator('Turbine Condenser',
              1,
              'Images/Blocks/Generators/Turbine Condenser.png',
              False,
              {},
              {'Power': 180, 'Water': 5},
              60), # Turbine Condenser
    Generator('Chemical Combustion Chamber',
              1,
              'Images/Blocks/Generators/Chemical Combustion Chamber.png',
              False,
              {'Ozone': 2, 'Arkycite': 40},
              {'Power': 550},
              60), # Chemical Combustion Chamber
    Generator('Pyrolysis Generator',
              1,
              'Images/Blocks/Generators/Pyrolysis Generator.png',
              False,
              {'Slag': 20, 'Arkycite': 40},
              {'Power': 1400, 'Water': 20},
              60), # Pyrolysis Generator
    Generator('Flux Reactor',
              1,
              'Images/Blocks/Generators/Flux Reactor.png',
              False,
              {'Cyanogen': 9, 'Heat': 150},
              {'Power': 15900},
              60), # Flux Reactor
    Generator('Neoplasia Reactor',
              1,
              'Images/Blocks/Generators/Neoplasia Reactor.png',
              False,
              {'Phase fabric': 1, 'Arkycite': 80, 'Water': 10},
              {'Power': 8400, 'Neoplasm': 20, 'Heat': 60},
              180), # Neoplasia Reactor
    UnitFactory('Ground Factory',
                0,
                72,
                'Images/Blocks/Unit production/Additive Reconstructor.png',
                {
                    'Dagger': None,
                    'Nova': None,
                    'Crawler': None
                },
                {
                    'Dagger': {'Silicon': 10, 'Lead': 10},
                    'Nova': {'Silicon': 30, 'Titanium': 20, 'Lead': 20},
                    'Crawler': {'Silicon': 8, 'Coal': 10}
                },
                {'Dagger': 15, 'Nova': 40, 'Crawler': 10}), # Ground Factory
    UnitFactory('Air Factory',
                0,
                72,
                'Images/Blocks/Unit production/Air Factory.png',
                {
                    'Flare': None,
                    'Poly': None
                },
                {
                    'Flare': {'Silicon': 15},
                    'Poly': {'Silicon': 30, 'Lead': 15}
                },
                {'Flare': 15, 'Poly': 35}), # Air Factory
    UnitFactory('Naval Factory',
                0,
                72,
                'Images/Blocks/Unit production/Naval Factory.png',
                {
                    'Risso': None,
                    'Retusa': None
                },
                {
                    'Risso': {'Silicon': 20, 'Metaglass': 35},
                    'Retusa': {'Silicon': 15, 'Titanium': 20}
                },
                {'Risso': 45, 'Retusa': 35}), # Naval Factory
    UnitFactory('Additive Reconstructor',
                0,
                180,
                'Images/Blocks/Unit production/Additive Reconstructor.png',
                {
                    'Mace': 'Dagger',
                    'Pulsar': 'Nova',
                    'Atrax': 'Crawler',
                    'Horizon': 'Flare',
                    'Poly': 'Mono',
                    'Minke': 'Risso',
                    'Oxynoe': 'Retusa'
                },
                {
                    'Mace': {'Silicon': 40, 'Graphite': 40},
                    'Pulsar': {'Silicon': 40, 'Graphite': 40},
                    'Atrax': {'Silicon': 40, 'Graphite': 40},
                    'Horizon': {'Silicon': 40, 'Graphite': 40},
                    'Poly': {'Silicon': 40, 'Graphite': 40},
                    'Minke': {'Silicon': 40, 'Graphite': 40},
                    'Oxynoe': {'Silicon': 40, 'Graphite': 40}
                },
                10), # Additive Reconstructor
    UnitFactory('Multiplicative Reconstructor',
                0,
                360,
                'Images/Blocks/Unit production/Multiplicative Reconstructor.png',
                {
                    'Fortress': 'Mace',
                    'Quasar': 'Pulsar',
                    'Spiroct': 'Atrax',
                    'Zenith': 'Horizon',
                    'Mega': 'Poly',
                    'Bryde': 'Minke',
                    'Cyerce': 'Oxynoe'
                },
                {
                    'Fortress': {'Silicon': 130, 'Titanium': 80, 'Metaglass': 40},
                    'Quasar': {'Silicon': 130, 'Titanium': 80, 'Metaglass': 40},
                    'Spiroct': {'Silicon': 130, 'Titanium': 80, 'Metaglass': 40},
                    'Zenith': {'Silicon': 130, 'Titanium': 80, 'Metaglass': 40},
                    'Mega': {'Silicon': 130, 'Titanium': 80, 'Metaglass': 40},
                    'Bryde': {'Silicon': 130, 'Titanium': 80, 'Metaglass': 40},
                    'Cyerce': {'Silicon': 130, 'Titanium': 80, 'Metaglass': 40}
                },
                30), # Multiplicative Reconstructor
    UnitFactory('Exponential Reconstructor',
                0,
                780,
                'Images/Blocks/Unit production/Exponential Reconstructor.png',
                {
                    'Scepter': 'Fortress',
                    'Vela': 'Quasar',
                    'Arkyid': 'Spiroct',
                    'Antumbra': 'Zenith',
                    'Quad': 'Mega',
                    'Sei': 'Bryde',
                    'Aegires': 'Oxynoe'
                },
                {
                    'Scepter': {'Silicon': 850, 'Titanium': 750, 'Plastanium': 650, 'Cryofluid': 60},
                    'Vela': {'Silicon': 850, 'Titanium': 750, 'Plastanium': 650, 'Cryofluid': 60},
                    'Arkyid': {'Silicon': 850, 'Titanium': 750, 'Plastanium': 650, 'Cryofluid': 60},
                    'Antumbra': {'Silicon': 850, 'Titanium': 750, 'Plastanium': 650, 'Cryofluid': 60},
                    'Quad': {'Silicon': 850, 'Titanium': 750, 'Plastanium': 650, 'Cryofluid': 60},
                    'Sei': {'Silicon': 850, 'Titanium': 750, 'Plastanium': 650, 'Cryofluid': 60},
                    'Aegires': {'Silicon': 850, 'Titanium': 750, 'Plastanium': 650, 'Cryofluid': 60}
                },
                90), # Exponential Reconstructor
    UnitFactory('Tetrative Reconstructor',
                0,
                1500,
                'Images/Blocks/Unit production/Tetrative Reconstructor.png',
                {
                    'Reign': 'Scepter',
                    'Corvus': 'Vela',
                    'Toxopid': 'Arkyid',
                    'Eclipse': 'Antumbra',
                    'Oct': 'Quad',
                    'Omura': 'Sei',
                    'Navanax': 'Aegires'
                },
                {
                    'Reign': {'Silicon': 1000, 'Plastanium': 600, 'Surge alloy': 500, 'Phase fabric': 350, 'Cryofluid': 180},
                    'Corvus': {'Silicon': 1000, 'Plastanium': 600, 'Surge alloy': 500, 'Phase fabric': 350, 'Cryofluid': 180},
                    'Toxopid': {'Silicon': 1000, 'Plastanium': 600, 'Surge alloy': 500, 'Phase fabric': 350, 'Cryofluid': 180},
                    'Eclipse': {'Silicon': 1000, 'Plastanium': 600, 'Surge alloy': 500, 'Phase fabric': 350, 'Cryofluid': 180},
                    'Oct': {'Silicon': 1000, 'Plastanium': 600, 'Surge alloy': 500, 'Phase fabric': 350, 'Cryofluid': 180},
                    'Omura': {'Silicon': 1000, 'Plastanium': 600, 'Surge alloy': 500, 'Phase fabric': 350, 'Cryofluid': 180},
                    'Navanax': {'Silicon': 1000, 'Plastanium': 600, 'Surge alloy': 500, 'Phase fabric': 350, 'Cryofluid': 180}
                },
                240), # Tetrative Reconstructor
    Block('Large Beryllium Wall',
          1,
          0,
          'Images/Blocks/Large Beryllium Wall.png'), # Large Beryllium Wall
    Block('Large Tungsten Wall',
          1,
          0,
          'Images/Blocks/Large Tungsten Wall.png'), # Large Tungsten Wall
    Block('Large Carbide Wall',
          1,
          0,
          'Images/Blocks/Large Carbide Wall.png'), # Large Carbide Wall
    Block('Large Reinforced Surge Wall',
          1,
          0,
          'Images/Blocks/Large Reinforced Surge Wall.png'), # Large Reinforced Surge Wall
    Block('Reinforced Container',
          1,
          0,
          'Images/Blocks/Reinforced Container.png'), # Reinforced Container
    Block('Reinforced Liquid Container',
          1,
          0,
          'Images/Blocks/Reinforced Liquid Container.png'), # Reinforced Liquid Container
    Block('Beam Node',
          1,
          0,
          'Images/Blocks/Beam Node.png'), # Beam Node
    UnitFactory('Constructor',
                1,
                120,
                'Images/Blocks/Unit production/Constructor.png',
                {
                    'Large Beryllium Wall': None,
                    'Large Tungsten Wall': None,
                    'Large Carbide Wall': None,
                    'Large Reinforced Surge Wall': None,
                    'Reinforced Container': None,
                    'Reinforced Liquid Container': None,
                    'Beam Node': None
                },
                {
                    'Large Beryllium Wall': {'Beryllium': 24},
                    'Large Tungsten Wall': {'Tungsten': 24},
                    'Large Carbide Wall': {'Carbide': 24, 'Thorium': 24},
                    'Large Reinforced Surge Wall': {'Surge alloy': 24, 'Tungsten': 8},
                    'Reinforced Container': {'Graphite': 40, 'Tungsten': 30},
                    'Reinforced Liquid Container': {'Beryllium': 16, 'Tungsten': 10},
                    'Beam Node': {'Beryllium': 8}
                },
                {
                    'Large Beryllium Wall': 2.4,
                    'Large Tungsten Wall': 3,
                    'Large Carbide Wall': 6,
                    'Large Reinforced Surge Wall': 4.08,
                    'Reinforced Container': 1.41,
                    'Reinforced Liquid Container': 0.57,
                    'Beam Node': 0.25
                }), # Constructor
    UnitFactory('Tank Fabricator',
                1,
                90,
                'Images/Blocks/Unit production/Tank Fabricator.png',
                {'Stell': None},
                {'Stell': {'Beryllium': 40, 'Silicon': 50}},
                35), # Tank Fabricator
    UnitFactory('Ship Fabricator',
                1,
                90,
                'Images/Blocks/Unit production/Ship Fabricator.png',
                {'Elude': None},
                {'Elude': {'Graphite': 50, 'Silicon': 70}},
                40), # Ship Fabricator
    UnitFactory('Mech Fabricator',
                1,
                90,
                'Images/Blocks/Unit production/Mech Fabricator.png',
                {'Merui': None},
                {'Merui': {'Beryllium': 50, 'Silicon': 70}},
                40), # Mech Fabricator
    UnitFactory('Tank Refabricator',
                1,
                180,
                'Images/Blocks/Unit production/Tank Refabricator.png',
                {'Locus': 'Stell'},
                {'Locus': {'Silicon': 40, 'Tungsten': 30, 'Hydrogen': 3}},
                30), # Tank Refabricator
    UnitFactory('Ship Refabricator',
                1,
                150,
                'Images/Blocks/Unit production/Ship Refabricator.png',
                {'Avert': 'Elude'},
                {'Avert': {'Silicon': 60, 'Tungsten': 40, 'Hydrogen': 3}},
                50), # Ship Refabricator
    UnitFactory('Mech Refabricator',
                1,
                150,
                'Images/Blocks/Unit production/Mech Refabricator.png',
                {'Cleroi': 'Merui'},
                {'Cleroi': {'Silicon': 50, 'Tungsten': 40, 'Hydrogen': 3}},
                45), # Mech Refabricator
    UnitFactory('Prime Refabricator',
                1,
                270,
                'Images/Blocks/Unit production/Prime Refabricator.png',
                {
                    'Precept': 'Locus',
                    'Obviate': 'Cleroi',
                    'Anthicus': 'Avert'
                },
                {
                    'Precept': {'Silicon': 100, 'Thorium': 80, 'Nitrogen': 10},
                    'Obviate': {'Silicon': 100, 'Thorium': 80, 'Nitrogen': 10},
                    'Anthicus': {'Silicon': 100, 'Thorium': 80, 'Nitrogen': 10}
                },
                60), # Prime Refabricator
    UnitFactory('Tank Assembler',
                1,
                180,
                'Images/Blocks/Unit production/Tank Assembler.png',
                {
                    'Vanquish': None,
                    'Conquer': None
                },
                {
                    'Vanquish': {'Stell': 4, 'Large Tungsten Wall': 10, 'Cyanogen': 9},
                    'Conquer': {'Locus': 6, 'Large Carbide Wall': 20, 'Cyanogen': 9}
                },
                {
                    'Vanquish': 50,
                    'Conquer': 180
                }), # Tank Assembler
    UnitFactory('Ship Assembler',
                1,
                180,
                'Images/Blocks/Unit production/Ship Assembler.png',
                {
                    'Quell': None,
                    'Disrupt': None
                },
                {
                    'Quell': {'Elude': 4, 'Large Beryllium Wall': 12, 'Cyanogen': 12},
                    'Disrupt': {'Avert': 6, 'Large Carbide Wall': 20, 'Cyanogen': 12}
                },
                {
                    'Quell': 60,
                    'Disrupt': 180
                }), # Ship Assembler
    UnitFactory('Mech Assembler',
                1,
                210,
                'Images/Blocks/Unit production/Mech Assembler.png',
                {
                    'Tecta': None,
                    'Collaris': None
                },
                {
                    'Tecta': {'Merui': 5, 'Large Tungsten Wall': 12, 'Cyanogen': 12},
                    'Collaris': {'Cleroi': 6, 'Large Carbide Wall': 20, 'Cyanogen': 12}
                },
                {
                    'Tecta': 70,
                    'Collaris': 180
                }), # Mech Assembler
    Factory('Water Extractor',
            0,
            90,
            'Images/Blocks/Extractors/Water Extractor.png',
            {},
            {'Water': 6.6},
            60), # Water Extractor
    Factory('Cultivator',
            0,
            80,
            'Images/Blocks/Item production/Cultivator.png',
            {'Water': 18},
            {'Spore pod': 1},
            80), # Cultivator
    Factory('Oil Extractor',
            0,
            180,
            'Images/Blocks/Extractors/Oil Extractor.png',
            {'Water': 9, 'Sand': 1},
            {'Oil': 15},
            60), # Oil Extractor
    Factory('Vent Condenser',
            1,
            30,
            'Images/Blocks/Extractors/Vent Condenser.png',
            {},
            {'Water': 30},
            60), # Vent Condenser
    Drill('Mechanical Drill',
          0,
          0,
          'Images/Blocks/Extractors/Mechanical Drill.png',
          {},
          {
              'Sand': 0.40,
              'Scrap': 0.40,
              'Copper': 0.36,
              'Lead': 0.36,
              'Coal': 0.34
          },
          ('Water', 3, 2.56)), # Mechanical Drill
    Drill('Pneumatic Drill',
          0,
          0,
          'Images/Blocks/Extractors/Pneumatic Drill.png',
          {},
          {
              'Sand': 0.6,
              'Scrap': 0.6,
              'Copper': 0.53,
              'Lead': 0.53,
              'Coal': 0.47,
              'Titanium': 0.43
          },
          ('Water', 3.6, 2.56)), # Pneumatic Drill
    Drill('Laser Drill',
          0,
          66,
          'Images/Blocks/Extractors/Laser Drill.png',
          {},
          {
              'Sand': 1.92,
              'Scrap': 1.92,
              'Copper': 1.63,
              'Lead': 1.63,
              'Coal': 1.42,
              'Titanium': 1.25,
              'Thorium': 1.12
          },
          ('Water', 4.8, 2.56)), # Laser Drill
    Drill('Airblast Drill',
          0,
          180,
          'Images/Blocks/Extractors/Airblast Drill.png',
          {},
          {
              'Sand': 3.42,
              'Scrap': 3.42,
              'Copper': 2.90,
              'Lead': 2.90,
              'Coal': 2.52,
              'Titanium': 2.23,
              'Thorium': 2.00
          },
          ('Water', 6, 3.24)), # Airblast Drill
    Drill('Plasma Bore',
          1,
          9,
          'Images/Blocks/Extractors/Plasma Bore.png',
          {},
          {
              'Beryllium': 0.75,
              'Graphite': 0.75
          },
          ('Hydrogen', 0.25, 2.5)), # Plasma Bore
    Drill('Advanced Plasma Bore',
          1,
          48,
          'Images/Blocks/Extractors/Advanced Plasma Bore.png',
          {'Hydrogen': 0.5},
          {
              'Beryllium': 1.8,
              'Graphite': 1.8,
              'Tungsten': 1.8,
              'Thorium': 1.8
          },
          ('Nitrogen', 3, 2.5)), # Advanced Plasma Bore
    Drill('Cliff Crusher',
          1,
          11,
          'Images/Blocks/Extractors/Cliff Crusher.png',
          {},
          {'Sand': 1.09}), # Cliff Crusher
    Drill('Advanced Cliff Crusher',
          1,
          60,
          'Images/Blocks/Extractors/Advanced Cliff Crusher.png',
          {'Hydrogen': 1},
          {'Sand': 3.75},
          ('Graphite', 0.75, 1.6)), # Advanced Cliff Crusher
    Drill('Impact Drill',
          1,
          160,
          'Images/Blocks/Extractors/Impact Drill.png',
          {'Water': 10},
          {
              'Beryllium': 2.66,
              'Tungsten': 1.33,
          },
          ('Ozone', 3, 1.75)), # Impact Drill
    Drill('Eruption Drill',
          1,
          360,
          'Images/Blocks/Extractors/Eruption Drill.png',
          {'Hydrogen': 4},
          {
              'Beryllium': 10.66,
              'Tungsten': 5.33,
              'Thorium': 5.33
          },
          ('Cyanogen', 0.75, 2)) # Eruption Drill
]

resources = [
    Item('Copper',
         0,
         blocks,
         ['Separator'],
         'Images/Items/Copper.png',
         True,
         True), # Copper
    Item('Lead',
         0,
         blocks,
         ['Separator'],
         'Images/Items/Lead.png',
         True,
         True), # Lead
    Item('Metaglass',
         0,
         blocks,
         ['Kiln'],
         'Images/Items/Metaglass.png',
         False), # Metaglass
    Item('Graphite',
         0,
         blocks,
         ['Separator', 'Graphite Press', find_block('Multi-Press')],
         'Images/Items/Graphite.png',
         False), # Graphite (Serpulo)
    Item('Sand',
         0,
         blocks,
         ['Pulverizer', 'Disassembler'],
         'Images/Items/Sand.png',
         True,
         True), # Sand (Serpulo)
    Item('Coal',
         0,
         blocks,
         ['Coal Centrifuge'],
         'Images/Items/Coal.png',
         True,
         True), # Coal
    Item('Titanium',
         0,
         blocks,
         ['Pneumatic Drill', 'Laser Drill', 'Airblast drill', 'Separator',
          'Disassembler'],
         'Images/Items/Titanium.png',
         True,
         False), # Titanium
    Item('Thorium',
         0,
         blocks,
         ['Laser Drill', 'Airblast Drill', 'Disassembler'],
         'Images/Items/Thorium.png',
         True,
         False), # Thorium (Serpulo)
    Item('Scrap',
         0,
         blocks,
         [],
         'Images/Items/Scrap.png',
         True,
         True), # Scrap
    Item('Silicon',
         0,
         blocks,
         ['Silicon Smelter', 'Silicon Crucible'],
         'Images/Items/Silicon.png',
         False), # Silicon (Serpulo)
    Item('Plastanium',
         0,
         blocks,
         ['Plastanium Compressor'],
         'Images/Items/Plastanium.png',
         False), # Plastanium
    Item('Phase fabric',
         0,
         blocks,
         ['Phase Weaver'],
         'Images/Items/Phase fabric.png',
         False), # Phase fabric (Serpulo)
    Item('Surge alloy',
         0,
         blocks,
         ['Surge Smelter'],
         'Images/Items/Surge alloy.png',
         False), # Surge alloy (Serpulo)
    Item('Spore pod',
         0,
         blocks,
         ['Cultivator'],
         'Images/Items/Spore pod.png',
         False), # Spore pod
    Item('Pyratite',
         0,
         blocks,
         ['Pyratite Mixer'],
         'Images/Items/Pyratite.png',
         False), # Pyratite
    Item('Blast compound',
         0,
         blocks,
         ['Blast Mixer'],
         'Images/Items/Blast compound.png',
         False), # Blast compound
    Item('Graphite',
         1,
         blocks,
         ['Plasma Bore', 'Large Plasma Bore'],
         'Images/Items/Graphite.png',
         True), # Graphite (Erekir)
    Item('Sand',
         1,
         blocks,
         ['Cliff Crusher', 'Advanced Cliff Crusher'],
         'Images/Items/Sand.png',
         True), # Sand (Erekir)
    Item('Thorium',
         1,
         blocks,
         ['Large Plasma Bore', 'Eruption Drill'],
         'Images/Items/Thorium.png',
         True), # Thorium (Erekir)
    Item('Silicon',
         1,
         blocks,
         ['Silicon Arc Furnace'],
         'Images/Items/Silicon.png',
         False), # Silicon (Erekir)
    Item('Phase fabric',
         1,
         blocks,
         ['Phase Synthesizer'],
         'Images/Items/Phase fabric.png',
         False), # Phase fabric (Erekir)
    Item('Surge alloy',
         1,
         blocks,
         ['Surge Crucible'],
         'Images/Items/Surge alloy.png',
         False), # Surge alloy (Erekir)
    Item('Beryllium',
         1,
         blocks,
         ['Plasma Bore', 'Large Plasma Bore', 'Impact Drill', 'Eruption Drill'],
         'Images/Items/Beryllium.png',
         True), # Beryllium
    Item('Tungsten',
         1,
         blocks,
         ['Large Plasma Bore', 'Impact Drill', 'Eruption Drill'],
         'Images/Items/Tungsten.png',
         True), # Tungsten
    Item('Oxide',
         1,
         blocks,
         ['Oxidation Chamber'],
         'Images/Items/Oxide.png',
         False), # Oxide
    Item('Carbide',
         1,
         blocks,
         ['Carbide Crucible'],
         'Images/Items/Carbide.png',
         False), # Carbide
    Fluid('Water',
          0,
          blocks,
          ['Water Extractor'],
          'Images/Items/Water.png',
          False,
          True), # Water (Serpulo)
    Fluid('Oil',
          0,
          blocks,
          ['Oil Extractor', 'Spore press'],
          'Images/Items/Oil.png',
          False,
          True), # Oil
    Fluid('Slag',
          0,
          blocks,
          ['Melter'],
          'Images/Items/Slag.png',
          False,
          True), # Slag (Serpulo)
    Fluid('Cryofluid',
          0,
          blocks,
          ['Cryofluid Mixer'],
          'Images/Items/Cryofluid.png',
          False,
          True), # Cryofluid
    Fluid('Water',
          1,
          blocks,
          ['Turbine Condenser', 'Vent Condenser', 'Pyrolysis Generator'],
          'Images/Items/Water.png',
          False,
          False), # Water (Erekir)
    Fluid('Slag',
          1,
          blocks,
          [],
          'Images/Items/Slag.png',
          False,
          True), # Slag (Erekir)
    Fluid('Arkycite',
          1,
          blocks,
          [],
          'Images/Items/Arkycite.png',
          False,
          True), # Arkycite
    Fluid('Neoplasm',
          1,
          blocks,
          ['Neoplasia Reactor'],
          'Images/Items/Neoplasm.png',
          False,
          False), # Neoplasm
    Fluid('Hydrogen',
          1,
          blocks,
          ['Electrolyzer'],
          'Images/Items/Hydrogen.png',
          True,
          False), # Hydrogen
    Fluid('Ozone',
          1,
          blocks,
          ['Electrolyzer'],
          'Images/Items/Ozone.png',
          True,
          False), # Ozone
    Fluid('Nitrogen',
          1,
          blocks,
          ['Atmospheric Condenser'],
          'Images/Items/Nitrogen.png',
          True,
          False), # Nitrogen
    Fluid('Cyanogen',
          1,
          blocks,
          ['Cyanogen Synthesizer'],
          'Images/Items/Cyanogen.png',
          True,
          False), # Cyanogen
]

units = [
    Unit('Dagger', 0, 'Images/Units/Dagger.png'),
    Unit('Mace', 0, 'Images/Units/Mace.png'),
    Unit('Fortress', 0, 'Images/Units/Fortress.png'),
    Unit('Scepter', 0, 'Images/Units/Scepter.png'),
    Unit('Reign', 0, 'Images/Units/Reign.png'),
    Unit('Crawler', 0, 'Images/Units/Crawler.png'),
    Unit('Atrax', 0, 'Images/Units/Atrax.png'),
    Unit('Spiroct', 0, 'Images/Units/Spiroct.png'),
    Unit('Arkyid', 0, 'Images/Units/Arkyid.png'),
    Unit('Toxopid', 0, 'Images/Units/Toxopid.png'),
    Unit('Nova', 0, 'Images/Units/Nova.png'),
    Unit('Pulsar', 0, 'Images/Units/Pulsar.png'),
    Unit('Quasar', 0, 'Images/Units/Quasar.png'),
    Unit('Vela', 0, 'Images/Units/Vela.png'),
    Unit('Corvus', 0, 'Images/Units/Corvus.png'),
    Unit('Flare', 0, 'Images/Units/Flare.png'),
    Unit('Horizon', 0, 'Images/Units/Horizon.png'),
    Unit('Zenith', 0, 'Images/Units/Zenith.png'),
    Unit('Antumbra', 0, 'Images/Units/Antumbra.png'),
    Unit('Eclipse', 0, 'Images/Units/Eclipse.png'),
    Unit('Mono', 0, 'Images/Units/Mono.png'),
    Unit('Poly', 0, 'Images/Units/Poly.png'),
    Unit('Mega', 0, 'Images/Units/Mega.png'),
    Unit('Quad', 0, 'Images/Units/Quad.png'),
    Unit('Oct', 0, 'Images/Units/Oct.png'),
    Unit('Risso', 0, 'Images/Units/Risso.png'),
    Unit('Minke', 0, 'Images/Units/Minke.png'),
    Unit('Bryde', 0, 'Images/Units/Bryde.png'),
    Unit('Sei', 0, 'Images/Units/Sei.png'),
    Unit('Omura', 0, 'Images/Units/Omura.png'),
    Unit('Retusa', 0, 'Images/Units/Retusa.png'),
    Unit('Oxynoe', 0, 'Images/Units/Oxynoe.png'),
    Unit('Cyerce', 0, 'Images/Units/Cyerce.png'),
    Unit('Aegires', 0, 'Images/Units/Aegires.png'),
    Unit('Navanax', 0, 'Images/Units/Navanax.png'),
    Unit('Stell', 1, 'Images/Units/Stell.png'),
    Unit('Locus', 1, 'Images/Units/Locus.png'),
    Unit('Precept', 1, 'Images/Units/Precept.png'),
    Unit('Vanquish', 1, 'Images/Units/Vanquish.png'),
    Unit('Conquer', 1, 'Images/Units/Conquer.png'),
    Unit('Merui', 1, 'Images/Units/Merui.png'),
    Unit('Cleroi', 1, 'Images/Units/Cleroi.png'),
    Unit('Anthicus', 1, 'Images/Units/Anthicus.png'),
    Unit('Tecta', 1, 'Images/Units/Tecta.png'),
    Unit('Collaris', 1, 'Images/Units/Collaris.png'),
    Unit('Elude', 1, 'Images/Units/Elude.png'),
    Unit('Avert', 1, 'Images/Units/Avert.png'),
    Unit('Obviate', 1, 'Images/Units/Obviate.png'),
    Unit('Quell', 1, 'Images/Units/Quell.png'),
    Unit('Disrupt', 1, 'Images/Units/Disrupt.png'),
]
