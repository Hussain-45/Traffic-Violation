import React, { useState, useContext } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import { AuthContext, API_BASE_URL } from "../App";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "../components/ui/card";
import { Lock, User, Eye, EyeOff, ShieldAlert, Sparkles, Building2 } from "lucide-react";

export default function Login() {
  const { login } = useContext(AuthContext);
  const navigate = useNavigate();
  const location = useLocation();

  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [forgotModal, setForgotModal] = useState(false);
  const [forgotEmail, setForgotEmail] = useState("");
  const [forgotMsg, setForgotMsg] = useState("");

  const redirectPath = location.state?.from?.pathname || "/dashboard";

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      const bodyParams = new URLSearchParams();
      bodyParams.append("username", username);
      bodyParams.append("password", password);

      const response = await fetch(`${API_BASE_URL}/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: bodyParams,
      });

      if (response.ok) {
        const data = await response.json();
        login(data.access_token, {
          role: data.role,
          full_name: data.full_name,
          username: username,
        });
        navigate(redirectPath, { replace: true });
      } else {
        const errData = await response.json();
        setError(errData.detail || "Authentication failed. Try again.");
      }
    } catch (err) {
      console.warn("Backend offline. Entering stand-alone demo mode.");
      // Fallback local authentication for standalone frontend demo
      if (
        (username === "admin" && password === "admin123") ||
        (username === "officer" && password === "officer123")
      ) {
        login("dummy-jwt-token", {
          username,
          full_name: username === "admin" ? "Super Admin" : "Officer Rajesh",
          role: username === "admin" ? "admin" : "officer",
        });
        navigate(redirectPath, { replace: true });
      } else {
        setError("Invalid username or password. (Demo: admin/admin123 or officer/officer123)");
      }
    } finally {
      setLoading(false);
    }
  };

  const handleForgotSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setForgotMsg(`Password reset link sent to ${forgotEmail} (Simulation Mode).`);
  };

  return (
    <div className="relative flex h-screen w-screen items-center justify-center bg-slate-950 text-slate-100 overflow-hidden">
      {/* Background Glows */}
      <div className="absolute top-[-20%] left-[-20%] h-[70vw] w-[70vw] rounded-full bg-blue-600/10 blur-[120px] animate-pulse"></div>
      <div className="absolute bottom-[-20%] right-[-20%] h-[70vw] w-[70vw] rounded-full bg-indigo-600/10 blur-[120px] animate-pulse" style={{ animationDelay: '2s' }}></div>

      <div className="relative z-10 w-full max-w-sm px-4">
        
        {/* Header */}
        <div className="flex flex-col items-center mb-6">
          <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-blue-600 shadow-xl shadow-blue-500/30 mb-2">
            <Building2 size={24} className="text-white" />
          </div>
          <h1 className="text-xl font-extrabold tracking-tight bg-gradient-to-r from-white via-slate-150 to-slate-400 bg-clip-text text-transparent">
            TRAFFIC CONTROL CENTER
          </h1>
          <p className="text-[10px] text-slate-400 font-bold uppercase tracking-widest mt-0.5">
            Delhi smart city governance
          </p>
        </div>

        {/* Card Component from ui/ */}
        <Card className="glass-panel border-white/10 shadow-2xl p-2">
          <CardHeader className="pb-4">
            <CardTitle className="text-sm font-bold text-white flex items-center gap-2">
              <Sparkles size={16} className="text-blue-400" />
              Portal Access Control
            </CardTitle>
            <CardDescription className="text-slate-400 text-[10px]">
              Provide credentials to verify command credentials.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            
            {error && (
              <div className="flex items-start gap-2.5 rounded-xl bg-red-500/10 border border-red-500/30 p-3 text-[11px] text-red-400">
                <ShieldAlert size={14} className="shrink-0 mt-0.5" />
                <span>{error}</span>
              </div>
            )}

            <form onSubmit={handleSubmit} className="space-y-3.5">
              <div className="space-y-1">
                <label className="text-[10px] font-bold uppercase tracking-wider text-slate-400">
                  Officer Username
                </label>
                <div className="relative">
                  <User size={16} className="absolute left-3.5 top-3 text-slate-500" />
                  <Input
                    type="text"
                    required
                    placeholder="Enter login name (e.g. officer)"
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                    className="pl-10 text-xs text-white"
                  />
                </div>
              </div>

              <div className="space-y-1">
                <div className="flex items-center justify-between">
                  <label className="text-[10px] font-bold uppercase tracking-wider text-slate-400">
                    Security Password
                  </label>
                  <button
                    type="button"
                    onClick={() => setForgotModal(true)}
                    className="text-[9px] font-bold text-blue-400 hover:text-blue-300"
                  >
                    Forgot Key?
                  </button>
                </div>
                <div className="relative">
                  <Lock size={16} className="absolute left-3.5 top-3 text-slate-500" />
                  <Input
                    type={showPassword ? "text" : "password"}
                    required
                    placeholder="Enter credentials password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className="pl-10 pr-10 text-xs text-white"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-3.5 top-3.5 text-slate-500 hover:text-slate-350 cursor-pointer"
                  >
                    {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
                  </button>
                </div>
              </div>

              <Button
                type="submit"
                disabled={loading}
                className="w-full text-xs font-bold py-3 mt-4"
              >
                {loading ? (
                  <div className="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent"></div>
                ) : (
                  "Authenticate Session"
                )}
              </Button>
            </form>

            <div className="pt-3 border-t border-slate-900 flex justify-between items-center text-[9px] text-slate-500">
              <span>Admin: <strong className="text-slate-400">admin / admin123</strong></span>
              <span>Officer: <strong className="text-slate-400">officer / officer123</strong></span>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Forgot Drawer Modal */}
      {forgotModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
          <Card className="glass-panel w-full max-w-xs border-white/10 shadow-xl p-4 space-y-3">
            <div>
              <CardTitle className="text-sm font-bold text-white">Reset Credentials Key</CardTitle>
              <CardDescription className="text-slate-400 text-[10px] mt-0.5">
                Submit your police registry email.
              </CardDescription>
            </div>

            {forgotMsg && (
              <div className="rounded-xl bg-blue-500/10 border border-blue-500/30 p-2.5 text-[10px] text-blue-400 font-bold">
                {forgotMsg}
              </div>
            )}

            <form onSubmit={handleForgotSubmit} className="space-y-3">
              <Input
                type="email"
                required
                placeholder="officer@smarttraffic.gov.in"
                value={forgotEmail}
                onChange={(e) => setForgotEmail(e.target.value)}
                className="text-xs text-white"
              />
              <div className="flex gap-2 justify-end text-[10px] font-bold">
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={() => {
                    setForgotModal(false);
                    setForgotMsg("");
                  }}
                >
                  Cancel
                </Button>
                <Button type="submit" size="sm">
                  Send Link
                </Button>
              </div>
            </form>
          </Card>
        </div>
      )}
    </div>
  );
}
