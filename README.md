# FastAPI Authentication System

A comprehensive authentication system built with FastAPI, featuring multi-user support, email verification, password reset functionality, and OTP-based phone verification.

## 🚀 Features

- **Multi-User Support**: Separate User1 and User2 services with distinct collections
- **User Registration & Login**: Secure user authentication with JWT tokens
- **Email Verification**: Automated email verification with HTML templates
- **Password Reset**: Secure password reset via email links
- **OTP Verification**: SMS-based OTP verification using Twilio
- **Redis Caching**: Fast data access with Redis integration
- **Token Blacklisting**: Secure logout with JWT token blacklisting
- **Background Tasks**: Asynchronous email and SMS sending
- **MongoDB Integration**: Scalable data storage with MongoDB

## 🛠️ Tech Stack

- **Backend**: FastAPI
- **Database**: MongoDB (Motor async driver)
- **Cache**: Redis
- **Email Service**: FastMail with Jinja2 templates
- **SMS Service**: Twilio
- **Authentication**: JWT with OAuth2
- **Password Hashing**: Secure password hashing utilities

## 📋 Prerequisites

- Python 3.8+
- MongoDB
- Redis
- Twilio Account (for SMS functionality)
- SMTP Server (for email functionality)

## ⚙️ Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/HATAKEkakshi/Auth.git
   cd Auth/app
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirement.txt
   ```

3. **Set up environment variables**
   
   Create a `.env` file in the root directory:
   ```env
   # Database Configuration
   REDIS_HOST=localhost
   REDIS_PORT=6379
   
   # Email Configuration
   MAIL_USERNAME=your-email@gmail.com
   MAIL_PASSWORD=your-app-password
   MAIL_FROM=your-email@gmail.com
   MAIL_FROM_NAME=Your App Name
   MAIL_SERVER=smtp.gmail.com
   MAIL_PORT=587
   MAIL_STARTTLS=true
   MAIL_SSL_TLS=false
   USE_CREDENTIALS=true
   VALIDATE_CERTS=true
   
   # Twilio Configuration
   TWILIO_SID=your-twilio-sid
   TWILIO_AUTH_TOKEN=your-twilio-auth-token
   TWILIO_NUMBER=your-twilio-phone-number
   
   # Security Configuration
   JWT_SECRET=your-super-secret-jwt-key
   JWT_ALGORITHM=HS256
   
   # App Configuration
   APP_NAME=Auth System
   APP_DOMAIN=localhost:8000
   ```

4. **Set up MongoDB**
   ```bash
   # Make sure MongoDB is running on localhost:27017
   # The system will automatically create 'auth' database with 'User1' and 'User2' collections
   ```

5. **Set up Redis**
   ```bash
   # Make sure Redis is running on localhost:6379
   ```

## 🏃‍♂️ Running the Application

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`

## 📖 API Documentation

Once the server is running, visit:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

## 🔐 API Endpoints

### User1 Endpoints (`/User1`)

| Method | Endpoint | Description | Authentication |
|--------|----------|-------------|----------------|
| POST | `/User1/create` | Create new user | ❌ |
| POST | `/User1/login` | User login | ❌ |
| GET | `/User1/` | Get user by ID | ✅ |
| GET | `/User1/verify` | Verify email | ❌ |
| GET | `/User1/forget_password` | Request password reset | ❌ |
| GET | `/User1/reset_password_form` | Password reset form | ❌ |
| POST | `/User1/reset_password` | Reset password | ❌ |
| POST | `/User1/otp_phone` | Generate OTP | ❌ |
| GET | `/User1/verify_otp_phone` | Verify OTP | ❌ |
| GET | `/User1/logout` | Logout user | ✅ |
| DELETE | `/User1/delete` | Delete user | ✅ |

### User2 Endpoints (`/User2`)

Similar endpoints available for User2 with `/User2` prefix.

## 📝 Usage Examples

### 1. User Registration

```bash
curl -X POST "http://localhost:8000/User1/create" \
  -H "Content-Type: application/json" \
  -d '{
    "first_name": "John",
    "last_name": "Doe",
    "email": "john.doe@example.com",
    "phone": "+1234567890",
    "country_code": "US",
    "password": "securepassword123"
  }'
```

### 2. User Login

```bash
curl -X POST "http://localhost:8000/User1/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=john.doe@example.com&password=securepassword123"
```

### 3. Get User Information

```bash
curl -X GET "http://localhost:8000/User1/?id=user-id-here" \
  -H "Authorization: Bearer your-jwt-token"
```

### 4. Generate OTP

```bash
curl -X POST "http://localhost:8000/User1/otp_phone" \
  -H "Content-Type: application/json" \
  -d '{
    "id": "user-id-here",
    "phone": "+1234567890"
  }'
```

## 🏗️ Project Structure

```
├── services/
│   ├── user.py              # Base UserService class
│   ├── user1.py             # User1Service implementation
│   ├── user2.py             # User2Service implementation
│   └── notifications.py     # Email and SMS service
├── routes/
│   ├── user1.py             # User1 API routes
│   └── user2.py             # User2 API routes
├── model/
│   └── model.py             # Pydantic models
├── config/
│   ├── database.py          # Database configuration
│   ├── redis.py             # Redis configuration
│   ├── notification.py      # Email/SMS settings
│   └── security.py          # JWT settings
├── helper/
│   └── utils.py             # Utility functions
├── Dependencies/
│   └── dependencies.py      # FastAPI dependencies
└── core/
    └── security.py          # OAuth2 configuration
```

## 🔧 Configuration

### Email Templates

Place your HTML email templates in the templates directory:
- `registration.html` - Welcome email template
- `mail_email_verify.html` - Email verification template
- `mail_password_reset.html` - Password reset template
- `email_verified.html` - Email verification success page
- `reset.html` - Password reset form
- `reset_success.html` - Password reset success page

### Security Features

- **Password Hashing**: Secure password hashing with salt
- **JWT Tokens**: Stateless authentication with configurable expiration
- **Token Blacklisting**: Secure logout functionality
- **Email Verification**: Mandatory email verification for new users
- **Rate Limiting**: Built-in protection against brute force attacks

## 🔍 Monitoring & Debugging

The application includes comprehensive logging for debugging:
- Email sending status
- SMS delivery confirmation
- Redis cache operations
- Authentication failures

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:
- Create an issue in the GitHub repository
- Check the API documentation at `/docs`
- Review the logs for debugging information

## 🔮 Future Enhancements

- [ ] Two-factor authentication (2FA)
- [ ] Social media login integration
- [ ] Rate limiting and throttling
- [ ] API versioning
- [ ] Comprehensive test suite
- [ ] Docker containerization
- [ ] Database migrations
- [ ] Admin dashboard

---

**Note**: This authentication system is production-ready but ensure you review and customize the security settings according to your specific requirements before deploying to production.
