import { Navigate, Route, Routes } from "react-router-dom";
import { ProtectedRoute } from "./components/ProtectedRoute";
import { AuthProvider, useAuth } from "./context/AuthContext";
import { VisitFlowProvider } from "./context/VisitFlowContext";
import { DebriefGeneratePage } from "./pages/DebriefGeneratePage";
import { DebriefReviewPage, SuccessPage } from "./pages/DebriefReviewPage";
import { GalleryPage } from "./pages/GalleryPage";
import { LandingPage } from "./pages/LandingPage";
import { LogVisitPage } from "./pages/LogVisitPage";
import { LoginPage } from "./pages/LoginPage";
import { ManagerPage } from "./pages/ManagerPage";
import { PreviousVisitsPage } from "./pages/PreviousVisitsPage";
import { ReviewNotesPage } from "./pages/ReviewNotesPage";
import { SettingsPage } from "./pages/SettingsPage";
import { SignupPage } from "./pages/SignupPage";

function HomeRedirect() {
  const { isAuthenticated, user } = useAuth();
  if (!isAuthenticated) return <LandingPage />;
  if (user?.role === "manager") return <Navigate to="/manager" replace />;
  return <Navigate to="/app/log" replace />;
}

export default function App() {
  return (
    <AuthProvider>
      <VisitFlowProvider>
        <Routes>
          <Route path="/" element={<HomeRedirect />} />
          <Route path="/login" element={<LoginPage />} />
          <Route path="/signup" element={<SignupPage />} />

          <Route element={<ProtectedRoute role="field_worker" />}>
            <Route path="/app/log" element={<LogVisitPage />} />
            <Route path="/app/log/review" element={<ReviewNotesPage />} />
            <Route path="/app/log/debrief/generate" element={<DebriefGeneratePage />} />
            <Route path="/app/log/debrief" element={<DebriefReviewPage />} />
            <Route path="/app/log/success" element={<SuccessPage />} />
            <Route path="/app/visits" element={<PreviousVisitsPage />} />
            <Route path="/app/gallery" element={<GalleryPage />} />
            <Route path="/app/settings" element={<SettingsPage />} />
          </Route>

          <Route element={<ProtectedRoute role="manager" />}>
            <Route path="/manager" element={<ManagerPage />} />
          </Route>

          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </VisitFlowProvider>
    </AuthProvider>
  );
}
