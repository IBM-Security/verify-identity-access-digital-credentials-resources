import React from "react";
import { Routes, Route } from "react-router-dom";
import { CssBaseline, ThemeProvider } from "@mui/material";
import theme from "./theme";

import LoginPage from "./pages/LoginPage";
import ProfilePage from "./pages/ProfilePage";

import ProtectedRoute from "./components/ProtectedRoute";
import Footer from "./components/Footer";
import { RedirectToLogin } from "./components/RedirectToLogin";
import OidcCallback from "./components/OidcCallback";
import { AuthProvider } from "./components/AuthProvider";

const App: React.FC = () => {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <AuthProvider>
        <div className="dmv-app">
          <Routes>
            <Route path="/" element={<RedirectToLogin />} />
            <Route path="/login" element={<LoginPage />} />
            <Route path="/profile" element={<ProtectedRoute><ProfilePage /></ProtectedRoute>} />
            <Route path="/logincallback" element={<OidcCallback />} />
            <Route path="*" element={<RedirectToLogin />} />
          </Routes>
          <Footer />
        </div>
      </AuthProvider>
    </ThemeProvider>
  );
};

export default App;
