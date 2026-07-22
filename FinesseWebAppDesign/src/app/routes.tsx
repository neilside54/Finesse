import { createBrowserRouter, RouterProvider, Outlet, Link, useLocation } from "react-router";
import { Home } from "./pages/Home";
import { AnalyzeUsername } from "./pages/AnalyzeUsername";
import { AnalyzePgn } from "./pages/AnalyzePgn";
import { TaskStatus } from "./pages/TaskStatus";
import { Results } from "./pages/Results";
import { Login } from "./pages/Login";
import { Register } from "./pages/Register";
import { History } from "./pages/History";
import { Support } from "./pages/Support";
import { Profile } from "./pages/Profile";
import { Layout } from "./components/Layout";

export const router = createBrowserRouter([
  {
    path: "/",
    Component: Layout,
    children: [
      { index: true, Component: Home },
      { path: "analyze/username", Component: AnalyzeUsername },
      { path: "analyze/pgn", Component: AnalyzePgn },
      { path: "status/:taskId", Component: TaskStatus },
      { path: "results/:taskId", Component: Results },
      { path: "login", Component: Login },
      { path: "register", Component: Register },
      { path: "history", Component: History },
      { path: "profile", Component: Profile },
      { path: "support", Component: Support },
    ],
  },
]);
