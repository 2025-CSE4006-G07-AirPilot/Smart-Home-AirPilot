# PuriPilot (English)

Most air purifiers rely only on **particulate matter** and **harmful gas sensors**.
Because of this, several issues occur:

1.	When users apply air fresheners, diffusers, fabric sprays, perfumes, or cosmetics,
  the purifier may overreact and absorb `harmless scent molecules`,
  `unnecessarily reducing filter lifespan`.
2.	Odors naturally `spread across multiple rooms`,
  but most products can control only a `single device`,
  and cannot `coordinate multiple purifiers` across a home.

PuriPilot is a smart-home AI project designed to solve these issues:
  1.	Using an e-nose (electronic nose), it learns `odor patterns` and increases the purifier mode only `when the smell is unpleasant` based on rule logic.
  2.	With a `Room-Graph` (room connection graph), it controls multiple purifiers `simultaneously and contextually`.
  3.	All system behavior can be `visualized and controlled on the web`.

In short: PuriPilot is a `smart-home floor-plan + 3D-style demo that can control LG PuriCare devices`,
designed for `ESP32 + sensors + Edge Impulse-based odor automation`.

## Key Features

PuriPilot enables:
  - 2D floor-plan editing
  - Placement of multiple LG PuriCare devices
  - Device information bubble showing:
    (id / name / mode / smell_class / last_seen)
  - Mode control directly from the UI
  - Persistent storage of floor plans and device data in MySQL
  - API exploration and testing via Swagger UI
  - ESP32 + e-nose + Edge Impulse integration for:
  - Odor pattern classification
  - Mode increase only for unpleasant smells
  - Multi-device control using Room-Graph

This repository serves as an `experimental / demo project` for:

  - Smart-home UI/UX (2D floor plan with 3D-like device placement)
  - Multi-device air purifier control
  - Integration of IoT devices (ESP32 + sensors + Edge Impulse) with the web backend

## Architecture Overview
**Frontend**
  - Runs under example/
  - 2D floor-plan editor
  Placement of LG PuriCare units
  Bubbles showing real-time device info and mode controls
**Backend**
  - Node.js + Express
  - MySQL storage for floor plans and device states
  -	REST API with Swagger UI

**IoT / Inference (addtional model training planned)**
  -	ESP32 + e-nose (temperature, humidity, gas sensors, etc.)
  -	Edge Impulse for odor / air-quality pattern classification
  -	Rule-based evaluation for “unpleasant smell”
  -	Room-Graph for coordinated control of multiple purifiers
  -	ESP32 sends device state and predictions to the backend

## Quick Start

### Requirements
  -	Node.js 18+
  -	MySQL instance (local or remote)

### Environment Setup

Create a `.env` file in the project root:
```
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=your_user
MYSQL_PASSWORD=your_password
MYSQL_DATABASE=puripilot_db
PORT=3001
```
> Note: PORT is the backend server port (default 3001),
> not the MySQL port.

### Installation & Run

```
# In project root
npm install

npm run start:server   # Starts backend, runs DB migration, seeds default lg-puricare-1
```

In another terminal:
```
cd example
npx http-server .      # Or any static server for the example/ folder
````

Then open:
-	Frontend: http://localhost:8080
-	Backend: http://localhost:3001
-	Swagger UI: http://localhost:3001/api/docs

## How to Use the App
1.	`Edit the floor plan`
  - Draw or modify your home layout in the 2D editor.
  - Press `Done` to automatically save the floor plan to the backend.

2.	Add LG PuriCare devices
  - `Use Add Items → Lg Puricare`.
  -	Each placement `creates one row` in MySQL.
  
3.	View and control devices
	-	Go to the `Design` tab.
	-	Select any `Lg Puricare` unit in the layout.
	-	Its bubble will show: id, name, mode, smell_class, last_seen
	-	Tap a mode button to send an instant `PATCH` request.
	-	Device names can also be edited and saved.

This allows users to `visualize device positions` and manage multiple purifiers easily from one screen.

## ESP32 + Edge Impulse Integration (Planned)

PuriPilot is designed to integrate smoothly with `real IoT devices`:

-	`ESP32` reads e-nose and other sensor data.
-	`Edge Impulse` model classifies `odor patterns`.
-	Rule logic determines:
    -	Whether the smell is `unpleasant`
    -	Whether to `increase purifier mode`
-	`Room-Graph` enables control of adjacent rooms affected by odor spread.
-	ESP32 periodically sends:
    -	Sensor data
    -	Predicted smell class
    -	Device state / timestamp to the backend, which updates `smell_class` and `last_seen`.

Future README updates will include:

	1.	Deploying Edge Impulse models to ESP32 via Arduino IDE
	2.	Sending inference results from ESP32 to the PuriPilot backend
	3.	Linking ESP32 devices with PuriPilot device_id and Room-Graph

## NPM Scripts
-	`npm run start:server` — Start Express + MySQL + Swagger
-	`npm run build` — Build the client (legacy browserify pipeline)
- `npx http-server example -p 8080 -c-1 -o index.html`

## Repository
```
git@github.com:PuriPilot/Smart-Home-PuriPilot.git
```