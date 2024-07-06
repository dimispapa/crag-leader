<h1 align="center">CRAG LEADER - Bouldering Leaderboard CLI app</h1>

"Crag Leader" is an application built on a command-line interface, with the purpose of scraping climbing logs from a widely used online platform called [27crags](https://27crags.com/crags/inia-droushia/).

![bouldering-image](documentation/images/ai-boulder-art.webp)
<br/>

This app aims to process the scraped information and it is capable of displaying a number of leaderboards depending on the chosen criteria (overall, volume, unique ascent etc.), with a pre-defined scoring system. The current prototype version is focused on my local bouldering crag in Inia & Droushia of Cyprus but wider use of the app on other crags of the same platform is possible with some minor adjustments.

<div style="text-align:center">
<a href="https://crag-leader-a9343167f108.herokuapp.com/">ACCESS THE APPLICATION</a></div>

<br/>

## Table of Contents

- [Table of Contents](#table-of-contents)
- [UX](#ux)
  - [App Purpose](#app-purpose)
  - [App Goals](#app-goals)
  - [Audience](#audience)
  - [Communication](#communication)
  - [Current User Goals](#current-user-goals)
  - [Future User Goals](#future-user-goals)
- [Logic](#logic)
  - [Process Flow Diagrams](#process-flow-diagrams)
- [Design](#design)
  - [Colour](#colour)
  - [Existing Features](#existing-features)
  - [Hidden Features](#hidden-features)
  - [Future Features](#future-features)
- [Testing](#testing)
  - [Validator Testing](#validator-testing)
  - [Fixed Bugs](#fixed-bugs)
  - [Unfixed Bugs](#unfixed-bugs)
- [Technologies Used](#technologies-used)
  - [Main Languages Used](#main-languages-used)
  - [Python Packages-Modules](#python-packages-modules)
  - [Tools](#tools)
- [Deployment](#deployment)
  - [How to deploy](#how-to-deploy)
  - [How to clone](#how-to-clone)
- [Credits](#credits)
- [Acknowledgements](#acknowledgements)

## UX

### App Purpose

This application was designed with the purpose of presenting the user with various leaderboards based on scraped or stored data from the 27crags online climbing platform.

### App Goals

- Gamify climbing and bouldering by generating friendly competition between climbers and increase motivation for climbing and maintaining an online log.
- Allow climbers to have visibility of their standings, progress and the levels accross the community.

### Audience

Narrow audience of climbers actively using the 27crags platform and specifically for climbers who log climbs at the Inia & Droushia crag in Cyprus.

### Communication

The application interacts with the user via prompts and print statements in the terminal. The user is presented with various choices and is asked to input their choices in the terminal.

UX is improved through the use of colour and progress bars, to communicate information in a clearer and more visually appealing manner.

### Current User Goals

- Scrape latest ascent data or fetch currently stored data for a faster loading time. The decision is to be made based on the last updated date.
- Present leaderboard rankings based on the chosen criteria.

### Future User Goals

- Provide another menu with options with interesting statistics about the crag, boulders, routes and ascents.
- Increase the audience by allowing logging of climbs via the CRAG LEADER app directly, while maintaining the capability to scrape data from 27crags, in order to allow both users and non-users of "27crags" to use CRAG LEADER.
- Increase the audience by allowing the choice of crag on start, in order to expand usage to all crags available on the "27crags" platform. This will also expand the usage to Sport Climbing or Traditional Climbing, other than just Bouldering.

## Logic

### Process Flow Diagrams

The following flowcharts were created using [Overleaf](https://www.overleaf.com/) to visualise the logical flow of the application.

- The structure and relationship between the user-created python modules reached its current state, as a result of continuous refactoring of code as the application grew and developed. Breaking it down into smaller and related elements of classes, functions and modules as the application was getting bigger, made it easier to reuse, debug, test and maintain.
![Python Relationship](documentation/diagrams/py-relation.png)

Drilling down further into specific classes, methods and functions:

- Main Functionality
![Main Function](documentation/diagrams/main-diagram.png)

- Google Sheets API Client
![Google Sheets API](documentation/diagrams/gsheets-diagram.png)

- Retrieve / Scrape Functionality
![Retrieve Scrape](documentation/diagrams/retrieve-scrape-diagram.png)

- Scraper Functionality
![Scraper Classes](documentation/diagrams/scaper-classes-diagram.png)

- Score Calculator Class
![Score Calculator Class](documentation/diagrams/score-diagram.png)

- Leaderboard Mode Functionality
![Leaderboard Mode](documentation/diagrams/leaderboard-diagram.png)

## Design

### Terminal Command-line interface (CLI)
The CLI was enhanced with the use of the *rich* python library. We have used the following classes from this library, initialised centrally from the *rich_utils.py* module and passed on to other modules as needed: 
  - **Console class**: Made use of the enhanced print method which allows the use of colour and emphasis. The following colours were used: 
     - Cyan Bold: Welcome and menu messages.
     - Yellow Bold: Progress updates.
     - Red Bold: Error and exiting messages.
     - Green: For the ASCII art welcome graphic.

  - **Progress class**: Creates a visually-appealing progress bar which is used during the running of the scraper to notify the user of progress, which normally takes 2-4 minutes depending on internet speed. A progress instance is initialised in the *rich_utils* module and passed over to the *run.py* file, where it is used with a context manager when the *scrape_data* function is called. The progress instance is used in the *crag.py* module, by adding a task just before looping through the boulder elements. The progress bar is able to estimate a percentage completion and time-to-completion, by reference to the *len* of the boulder elements list and the advancing by one each time it loops through one boulder. An example progress bar is below:
     - ![Progress Bar](documentation/screenshots/progess-bar.png)

  - **Table class**: Used for displaying the leaderboards in a more visually-appealing table format instead of the simple print method. The *display_table* function was created in the *rich_utils* module which is reused for displaying the leaderboard tables in the *run* module.

Furthermore, the ASCII art title "Crag Leader" on the welcome screen, was created using the python library *pyfiglet* and the font "doom" was chosen. The art was printed with green bold to add an "electrifying" feel to the welcome screen.

