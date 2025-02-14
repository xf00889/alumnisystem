# NORSU Alumni Web Portal

> ⚠️ **Note:** This project is currently under development.

A comprehensive web platform for Negros Oriental State University (NORSU) alumni to connect, network, and stay engaged with their alma mater.

## Features

- **Alumni Directory**: Search and connect with fellow alumni
- **Alumni Groups**: Create and join groups based on batch, course, or interests
- **Events Management**: Post and participate in alumni events and gatherings
- **Chat System**: Real-time communication between alumni
- **Announcements**: Stay updated with university and alumni news
- **Profile Management**: Showcase educational and professional achievements

## Technology Stack

- **Backend**: Django 4.2
- **Frontend**: HTML5, CSS3, JavaScript
- **Database**: SQLite (Development) / PostgreSQL (Production)
- **Real-time Communication**: Django Channels
- **Authentication**: Django Authentication System

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/xf00889/alumnisystem.git
   cd alumnisystem
   ```

2. Create and activate virtual environment:
   ```bash
   python -m venv venv
   
   # Windows
   venv\Scripts\activate
   
   # Linux/Mac
   source venv/bin/activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Set up environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. Run migrations:
   ```bash
   python manage.py migrate
   ```

6. Create superuser:
   ```bash
   python manage.py createsuperuser
   ```

7. Run the development server:
   ```bash
   python manage.py runserver
   ```

## Project Structure

```
alumnisystem/
├── accounts/          # User authentication and profiles
├── alumni_directory/  # Alumni listing and search
├── alumni_groups/     # Group management
├── announcements/     # News and updates
├── chat/             # Real-time messaging
├── events/           # Event management
├── core/             # Core functionality
└── templates/        # HTML templates
```

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## Security

- Protected user data and privacy
- Secure authentication system
- Regular security updates
- Input validation and sanitization

## Support

For support, please contact the development team or create an issue in the repository.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

---
Developed for Negros Oriental State University © 2024
