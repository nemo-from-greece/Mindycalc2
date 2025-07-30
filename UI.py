import customtkinter as ctk
import Data, Logic
import customwidgets as cw

class PlanetMenu(ctk.CTkFrame):
    def __init__(self, master, on_planet_selected, go_back):
        super().__init__(master)
        self.onPlanetSelected = on_planet_selected
        self.goBack = go_back
        self.onBackArgs = (on_planet_selected, go_back)
        self.create_widgets()

    def create_widgets(self):
        ctk.CTkLabel(self, text='Select a planet:').grid(pady=10, padx=10)

        planets = [str(i).split('.')[1].lower().capitalize() for i in Data.Planet]
        planets.append('Mixtech')

        for planet in planets:
            cw.DefaultButton(
                self, text=planet, width=60, height=25,
                command=lambda p=planet: self.onPlanetSelected(p)
            ).grid(pady=5, padx=10, sticky='ew')

class CategoryMenu(ctk.CTkFrame):
    def __init__(self, master, on_category_selected, go_back):
        super().__init__(master)
        self.onCategorySelected = on_category_selected
        self.goBack = go_back
        self.onBackArgs = (on_category_selected, go_back)
        self.create_widgets()

    def create_widgets(self):
        ctk.CTkLabel(self, text='Select what you want to produce:').grid(pady=10, padx=10)

        categories = ['Resources', 'Units', 'Power', 'Turrets']
        for category in categories:
            cw.DefaultButton(
                self, text=category, width=80, height=25,
                command=lambda c=category: self.onCategorySelected(c)
            ).grid(pady=5, padx=10, sticky='ew')

        cw.BackButton(self, self.goBack).grid(pady=(5, 20), padx=10, sticky='ew')

class FinalProductMenu(ctk.CTkFrame):
    def __init__(self, master, category, planetFilter, onItemSelected, goBack):
        super().__init__(master)
        self.category = category
        self.planetFilter = planetFilter
        self.onItemSelected = onItemSelected
        self.goBack = goBack
        self.onBackArgs = (category, planetFilter, onItemSelected, goBack)
        self.create_widgets()

    def create_widgets(self):
        if self.category != 'Power':
            ctk.CTkLabel(self, text=f'Select a {self.category[:-1].lower()} to produce').grid(
                pady=10, padx=10)
        else:
            ctk.CTkLabel(self, text='Select a generator').grid(pady=10)

        if self.category == 'Resources':
            items = Data.resources
        elif self.category == 'Units':
            items = Data.units
        elif self.category == 'Power':
            from Data import Generator
            items = [b for b in Data.blocks if isinstance(b, Generator)]
        elif self.category == 'Turrets':
            from Data import Turret
            items = [b for b in Data.blocks if isinstance(b, Turret)]
        else:
            items = []

        if self.planetFilter.lower() != 'mixtech':
            planetEnum = Data.Planet[self.planetFilter.upper()]
            items = [item for item in items if item.planet == planetEnum]

        gridFrame = ctk.CTkFrame(self)
        gridFrame.grid(sticky='nsew', padx=10, pady=10)

        if self.planetFilter.lower() != 'mixtech':
            for i, item in enumerate(items):
                frame = self.make_item_button(gridFrame, item)
                if self.category == 'Units':
                    frame.grid(row=i % 5, column=i // 5, padx=8, pady=8)
                else:
                    frame.grid(row=i // 4, column=i % 4, padx=8, pady=8)
        else:
            itemsPlaced = []
            count = -1
            for item in items:
                if item.name not in itemsPlaced:
                    count += 1
                    frame = self.make_item_button(gridFrame, item)
                    itemsPlaced.append(item.name)
                    if self.category == 'Units':
                        frame.grid(row=count % 5, column=count // 5, padx=8, pady=8)
                    else:
                        frame.grid(row=count // 4, column=count % 4, padx=8, pady=8)

        cw.BackButton(self, self.goBack).grid(pady=(5, 20))

    def make_item_button(self, parent, item):
        frame = ctk.CTkFrame(parent)
        cw.ITButton(frame, item.image, item.name, lambda: self.onItemSelected(item)).grid()
        return frame

class ProductionCalculatorMenu(ctk.CTkFrame):
    def __init__(self, master, category, planet, item, go_back):
        super().__init__(master)
        self.category = category
        self.planet = planet
        self.item = item
        self.goBack = go_back
        self.create_widgets()

    # noinspection PyAttributeOutsideInit
    def create_widgets(self):

        def print_output(rate, factory):
            string = 'You need ' + str(rate.get()) + ' ' + factory.name
            if float(rate.get()) != 1:
                string += 's'
            print(string)

        # Output Display
        titleFrame = ctk.CTkFrame(self)
        titleFrame.grid(row=0, column=0, columnspan=2)
        ctk.CTkLabel(titleFrame, text=self.item.name).grid(row=0, column=0, pady=5, padx=(5, 25))
        uiProductImage = Data.load_image(self.item.image)
        ctk.CTkLabel(titleFrame, image=uiProductImage, text='').grid(row=0, column=1, pady=5,
                                                                     padx=(25, 5))

        if self.category == 'Resources':
            maxVal = 10000.0
        elif self.category == 'Power':
            maxVal = 1000000.0
        else:
            maxVal = 1000.0

        self.extrasFrame = ctk.CTkFrame(self)
        self.extrasFrame.grid(sticky='nsew', padx=10, pady=10, row=1, column=0, columnspan=2)

        # Output Rate Spinbox
        ctk.CTkLabel(self.extrasFrame, text="Desired Output Rate:").grid(row=0, column=0,
                                                                        sticky="w",  padx=5)
        self.rate = cw.Spinbox(self.extrasFrame, maxValue=maxVal)
        self.rate.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        ctk.CTkLabel(self, text='Select production method').grid(row=2, column=0, sticky='ew',
                                                                 padx=5)

        # Inputs Frame
        inputsFrame = ctk.CTkFrame(self)
        inputsFrame.grid(row=2, column=0, columnspan=2, pady=10, sticky="nsew")

        if self.category == 'Resources':
            producers = Logic.find_producers_resource(self.item, self.planet)
            for i in producers:
                blockImage = Data.load_image(i.image)
                countLabel = cw.MathLabel(inputsFrame, self.rate.var, lambda x, factory=i:
                Logic.calculate_factory_count(factory, x, self.item.name))
                choiceButton = ctk.CTkButton(inputsFrame, image=blockImage, text='',
                                             command=lambda factory=i, var=countLabel.compVar:
                                             print_output(var, factory))
                choiceButton.grid(row=producers.index(i), column=0, padx=5, pady=5)
                countLabel.grid(row=producers.index(i), column=1, padx=5, pady=5)

        if self.category == 'Units':
            pass

        if self.category == 'Power':
            pass

        if self.category == 'Turrets':
            pass

        cw.BackButton(self, self.goBack).grid(row=99, column=0, columnspan=2, pady=(5, 20))

# noinspection PyAttributeOutsideInit
class AppUI(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title('Mindycalc')

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.container = ctk.CTkFrame(self)
        self.container.grid(row=0, column=0, sticky="nsew")

        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)

        self.frames = {}
        self.screenHistory = []
        self.context = {}

        self.show_planet_menu()

    def switch_screen(self, newScreenClass, *args):
        if hasattr(self, 'currentScreen') and self.currentScreen:
            self.screenHistory.append((type(self.currentScreen), self.currentScreen.onBackArgs))
            self.currentScreen.grid_forget()
            self.currentScreen.destroy()

        self.currentScreen = newScreenClass(self.container, *args)
        self.currentScreen.grid(row=0, column=0, sticky="nsew")

    def go_back(self):
        if self.screenHistory:
            screenClass, args = self.screenHistory.pop()
            self.currentScreen.grid_forget()
            self.currentScreen.destroy()
            self.currentScreen = screenClass(self.container, *args)
            self.currentScreen.grid(row=0, column=0, sticky="nsew")

    def show_planet_menu(self):
        self.switch_screen(PlanetMenu, self.handle_planet_selection, self.go_back)

    def show_category_menu(self):
        self.switch_screen(CategoryMenu, self.handle_category_selection, self.go_back)

    def handle_planet_selection(self, planet):
        self.context['planet'] = planet
        self.show_category_menu()

    def handle_category_selection(self, category):
        self.context['category'] = category
        self.switch_screen(
            FinalProductMenu,
            category,
            self.context['planet'],
            self.handle_item_selection,
            self.go_back
        )

    def handle_item_selection(self, item):
        self.context['item'] = item
        self.switch_screen(
            ProductionCalculatorMenu,
            self.context['category'], self.context['planet'],
            item,
            self.go_back
        )

    def next_step(self):
        pass
        # TODO: Implement the next step of the process. To this point, we have selected a final
        #  product and determined its output rate. We also have begun to populate the list of
        #  things needed to be calculated recursively.
