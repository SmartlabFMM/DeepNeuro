# Frontend - DeepNeuro Brain Disease Diagnosis

A modern desktop application built with PySide6 (Qt6) for brain disease diagnosis with advanced 3D visualization capabilities.

## Overview

The Frontend provides a rich graphical user interface for medical professionals to interact with the DeepNeuro AI-powered diagnosis system. It features user authentication, multiple diagnosis workflows, and sophisticated 3D segmentation visualization for brain tumor analysis.

## Architecture

### Core Components

- **`main.py`** - Application entry point, initializes the Qt application and launches the authentication window
- **`auth_window.py`** - Complete authentication system with login, signup, email verification, and password reset
- **`landing_page.py`** - Main dashboard after login, provides access to different diagnosis types
- **`segmentation_viewer.py`** - Advanced 3D viewer for brain tumor segmentation visualization using PyVista/VTK
- **`api_client.py`** - Singleton API client for all backend communication
- **`debug_database.py`** - Development utility for database inspection

## Features

### 🔐 User Authentication
- Secure login/signup system
- Email verification workflow
- Password reset functionality
- Remember me option
- Session management

### 🏠 Landing Dashboard
- User-specific welcome interface
- Multiple diagnosis type selection:
  - Glioma Tumor (with 3D segmentation)
  - Hemorrhagic Stroke
  - Ischemic Stroke
- User profile information
- Logout functionality

### 🧠 3D Segmentation Viewer
- Interactive 3D visualization of brain MRI data
- Support for NIfTI format (`.nii.gz` files)
- Layer-based segmentation display:
  - Brain Surface
  - Necrotic/Non-enhancing Tumor
  - Edema
  - Enhancing Tumor
  - Resection Cavity
- Toggle individual segmentation layers
- Real-time 3D rendering with PyVista/VTK
- File import from local filesystem

## Prerequisites

- Python 3.8 or higher
- Backend server running (see `Backend/README.md`)
- NIfTI brain scan files for segmentation viewing

## Installation

### 1. Navigate to Frontend Directory
```powershell
cd Frontend
```

### 2. Install Dependencies
```powershell
pip install -r requirements.txt
```

### Dependencies Overview
- **PySide6** - Qt6 framework for GUI
- **requests** - HTTP client for API communication
- **python-dotenv** - Environment variable management
- **nibabel** - NIfTI medical image file I/O
- **numpy** - Numerical computations
- **scikit-image** - Image processing utilities
- **pyvista** - 3D visualization library
- **pyvistaqt** - Qt integration for PyVista
- **vtk** - Visualization Toolkit for 3D graphics

## Running the Application

### Start the Frontend
```powershell
python main.py
```

The application will:
1. Launch with maximized window
2. Display the authentication screen
3. Connect to the backend API (default: `http://localhost:5000`)

### Environment Configuration
Create a `.env` file in the Frontend directory (optional):
```env
API_BASE_URL=http://localhost:5000
```
