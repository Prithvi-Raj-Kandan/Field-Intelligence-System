import { Navigate, Route, Routes } from "react-router-dom";
import { ProtectedRoute } from "./components/ProtectedRoute";
import { VisitFlowGuard } from "./components/VisitFlowGuard";
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
import { RecordingsPage } from "./pages/RecordingsPage";
import { ReviewNotesPage } from "./pages/ReviewNotesPage";
import { SettingsPage } from "./pages/SettingsPage";
import { SignupPage } from "./pages/SignupPage";
import { VisitDetailPage } from "./pages/VisitDetailPage";

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
            <Route
              path="/app/log/review"
              element={
                <VisitFlowGuard allowed={["notes_review"]}>
                  <ReviewNotesPage />
                </VisitFlowGuard>
              }
            />
            <Route
              path="/app/log/debrief/generate"
              element={
                <VisitFlowGuard allowed={["generating"]}>
                  <DebriefGeneratePage />
                </VisitFlowGuard>
              }
            />
            <Route
              path="/app/log/debrief"
              element={
                <VisitFlowGuard allowed={["debrief_review"]}>
                  <DebriefReviewPage />
                </VisitFlowGuard>
              }
            />
            <Route path="/app/log/success" element={<SuccessPage />} />
            <Route path="/app/visits" element={<PreviousVisitsPage />} />
            <Route path="/app/visits/:visitId" element={<VisitDetailPage />} />
            <Route path="/app/gallery" element={<GalleryPage />} />
            <Route path="/app/recordings" element={<RecordingsPage />} />
            <Route path="/app/settings" element={<SettingsPage />} />
          </Route>

          <Route element={<ProtectedRoute role="manager" />}>
            <Route path="/manager" element={<ManagerPage />} />
            <Route path="/dashboard" element={<ManagerPage />} />
          </Route>

          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </VisitFlowProvider>
    </AuthProvider>
  );
}
