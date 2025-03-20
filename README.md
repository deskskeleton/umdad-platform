# Modular Experiment Platform

A flexible and modular platform for running online experiments, particularly focused on economic and behavioral experiments.

## Features

- **Modular Design**: Easily add new experiment types with a plugin architecture
- **Access Control**: Generate unique access keys for experiment participants
- **Database Storage**: All experiment data is securely stored in PostgreSQL
- **Admin Interface**: Manage experiments, generate keys, and view results
- **Docker Support**: Easy deployment with Docker Compose

## Experiment Types

- **Prisoner's Dilemma**: A classic game theory experiment where participants decide to cooperate or defect
- (More experiments can be added following the modular architecture)

## Getting Started

### Prerequisites

- Docker and Docker Compose (for containerized setup)
- Python 3.9+ (for local development)
- PostgreSQL (for local development without Docker)

### Installation and Setup

1. **Clone the repository**

```bash
git clone https://github.com/yourusername/experiment-platform.git
cd experiment-platform
```

2. **Configure environment variables**

```bash
cp .env.example .env
# Edit .env with your configurations
```

3. **Run with Docker Compose**

```bash
docker-compose up -d
```

The application will be available at http://localhost:5000

4. **Create initial admin user**

```bash
docker-compose exec web python -m app.create_admin admin password admin@example.com
```

### Local Development Setup

1. **Create a virtual environment**

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. **Install dependencies**

```bash
pip install -r requirements.txt
```

3. **Configure local PostgreSQL and environment variables**

```bash
cp .env.example .env
# Edit .env with your local PostgreSQL settings
```

4. **Initialize the database**

```bash
python -m app.db.init_db
```

5. **Create an admin user**

```bash
python -m app.create_admin admin password admin@example.com
```

6. **Run the application**

```bash
python run.py
```

## Project Structure

```
experiment-platform/
├── app/                    # Application code
│   ├── admin/              # Admin interface
│   ├── auth/               # Authentication functionality
│   ├── db/                 # Database utilities
│   ├── experiments/        # Experiment modules
│   ├── static/             # Static assets
│   └── templates/          # HTML templates
├── .env.example            # Example environment variables
├── docker-compose.yml      # Docker Compose configuration
├── Dockerfile              # Docker configuration
├── requirements.txt        # Python dependencies
├── run.py                  # Application entry point
└── README.md               # This file
```

## Adding New Experiments

To add a new experiment type:

1. Create a new module in the `app/experiments/` directory
2. Implement the required interfaces (see examples in existing experiments)
3. Register your experiment in `app/experiments/__init__.py`

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgements

- [oTree](https://www.otree.org/) - A powerful open-source framework for behavioral economics experiments which inspired our modular architecture and experiment flow
- [z-Tree](https://www.ztree.uzh.ch/) - The Zurich Toolbox for Ready-made Economic Experiments
- [alter_ego](https://github.com/mgbckr/alter_ego) - A toolkit for integrating LLMs into experimental games
- [LEXI](https://github.com/stanford-policylab/LEXI) - LLM Experimentation Interface that influenced our approach to AI agent integration
- [Flask](https://flask.palletsprojects.com/) - The web framework used for the backend
- [PostgreSQL](https://www.postgresql.org/) - The database system for storing experiment data
- [Bootstrap](https://getbootstrap.com/) - For responsive UI components
- [Chart.js](https://www.chartjs.org/) - For data visualization in experiment results
- [Docker](https://www.docker.com/) - For containerization and simplified deployment
- [Maastricht University DSRI](https://docs.dh.unimaas.nl/category/dsri/) - Data Science Research Infrastructure for deployment
- The behavioral economics research community for their open-source contributions and experimental methodologies 
