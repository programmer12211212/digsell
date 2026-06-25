# AI-powered Digital Marketplace Platform (Digsell.uz)

Production-ready digital marketplace with AI integration, modern UI, and robust backend.

## 🚀 Quick Start (Docker)

1.  **Environment Setup**:
    ```bash
    cp .env.example .env  # Edit your keys
    ```

2.  **Run with Docker**:
    ```bash
    docker-compose up --build
    ```

3.  **Create Superuser**:
    ```bash
    docker-compose exec web python manage.py createsuperuser
    ```

## 🛠 Tech Stack
- **Backend**: Django 5.1, DRF
- **Frontend**: HTMX, Alpine.js, Tailwind CSS
- **Database**: PostgreSQL, Redis (Cache/Queue)
- **AI**: OpenAI GPT-4 Service Layer
- **Realtime**: Django Channels (WebSockets)
- **Tasks**: Celery + RabbitMQ/Redis

## 📂 Key Modules
- `apps/users`: Custom roles, 2FA, activity tracking.
- `apps/marketplace`: Digital products, versioning, secure downloads.
- `apps/ai_system`: Smart moderation, SEO generation, analytics.
- `apps/orders`: Escrow payments, subscriptions.

## 🎨 UI/UX Features
- **Glassmorphism**: Modern frosted-glass design.
- **Dark Mode**: Premium midnight aesthetic.
- **Micro-animations**: Smooth transitions using Alpine.js.
- **Lucide Icons**: Crisp, professional iconography.

Developed by Senior AI Software Architect.
