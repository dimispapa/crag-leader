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
- Allow climbers to have visibility of their standing and the levels accross the community.

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

The following flowcharts were created using [Overleaf](https://www.overleaf.com/) to visualise the logical flow of the application, drilling down to specific classes, methods or functions were required.

- Main Function
![Main Function](documentation/diagrams/main-diagram.png)