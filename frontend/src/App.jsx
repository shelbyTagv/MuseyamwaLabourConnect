import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { Toaster } from "react-hot-toast";
import useAuthStore from "./hooks/useAuth";

import Layout from "./components/Layout";
import Login from "./pages/Login";
import Register from "./pages/Register";
import EmployerDashboard from "./pages/EmployerDashboard";
import EmployeeDashboard from "./pages/EmployeeDashboard";
import AdminDashboard from "./pages/AdminDashboard";
import JobDetail from "./pages/JobDetail";
import TokenWallet from "./pages/TokenWallet";
import Chat from "./pages/Chat";
import Profile from "./pages/Profile";
import HeatMap from "./pages/HeatMap";
import Landing from "./pages/Landing";

function ProtectedRoute({ children, roles }) {
    const { isAuthenticated, user } = useAuthStore();
    if (!isAuthenticated) return <Navigate to="/login" />;
    if (roles && !roles.includes(user?.role)) return <Navigate to="/" />;
    return children;
}

export default function App() {
    const { isAuthenticated, user } = useAuthStore();

    const getDashboardRedirect = () => {
        if (!isAuthenticated) return "/login";
        switch (user?.role) {
            case "admin": return "/admin";
            case "employer": return "/employer";
            case "employee": return "/employee";
            default: return "/login";
        }
    };

    return (
        <BrowserRouter>
            <Toaster
                position="top-right"
                toastOptions={{
                    style: {
                        background: "#292524",
                        color: "#fff",
                        border: "1px solid rgba(255,255,255,0.1)",
                    },
                }}
            />
            <Routes>
                {/* Public */}
                <Route path="/" element={isAuthenticated ? <Navigate to={getDashboardRedirect()} /> : <Landing />} />
                <Route path="/login" element={<Login />} />
                <Route path="/register" element={<Register />} />

                {/* Protected – Employer */}
                <Route path="/employer" element={<ProtectedRoute roles={["employer"]}><Layout><EmployerDashboard /></Layout></ProtectedRoute>} />
                <Route path="/employer/map" element={<ProtectedRoute roles={["employer"]}><Layout><HeatMap /></Layout></ProtectedRoute>} />

                {/* Protected – Employee */}
                <Route path="/employee" element={<ProtectedRoute roles={["employee"]}><Layout><EmployeeDashboard /></Layout></ProtectedRoute>} />

                {/* Protected – Admin */}
                <Route path="/admin" element={<ProtectedRoute roles={["admin"]}><Layout><AdminDashboard /></Layout></ProtectedRoute>} />

                {/* Shared Protected */}
                <Route path="/jobs/:id" element={<ProtectedRoute><Layout><JobDetail /></Layout></ProtectedRoute>} />
                <Route path="/tokens" element={<ProtectedRoute><Layout><TokenWallet /></Layout></ProtectedRoute>} />
                <Route path="/chat" element={<ProtectedRoute><Layout><Chat /></Layout></ProtectedRoute>} />
                <Route path="/chat/:partnerId" element={<ProtectedRoute><Layout><Chat /></Layout></ProtectedRoute>} />
                <Route path="/profile" element={<ProtectedRoute><Layout><Profile /></Layout></ProtectedRoute>} />
                <Route path="/profile/:userId" element={<ProtectedRoute><Layout><Profile /></Layout></ProtectedRoute>} />

                {/* Catch-all */}
                <Route path="*" element={<Navigate to="/" />} />
            </Routes>
        </BrowserRouter>
    );
}
