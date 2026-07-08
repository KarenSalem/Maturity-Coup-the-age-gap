import React, { useEffect, useState } from "react";
import HomePage from "./pages/HomePage";
import DrivingCostsPage from "./pages/DrivingCostsPage";
import PolishedPage from "./pages/PolishedPage";
import OverlayExperimentPage from "./pages/OverlayExperimentPage";
import TeenAutonomyPage from "./pages/TeenAutonomyPage";
import TeenAutonomyFigure1EmbedPage from "./pages/TeenAutonomyFigure1EmbedPage";

function getPathname() {
  if (typeof window === "undefined") {
    return "/";
  }

  return window.location.pathname.replace(/\/+$/, "") || "/";
}

export default function App() {
  const [pathname, setPathname] = useState(getPathname);

  useEffect(() => {
    const handlePopState = () => {
      setPathname(getPathname());
    };

    window.addEventListener("popstate", handlePopState);
    return () => window.removeEventListener("popstate", handlePopState);
  }, []);

  if (pathname === "/polished") {
    return <PolishedPage />;
  }

  if (pathname === "/driving-costs") {
    return <DrivingCostsPage />;
  }

  if (pathname === "/overlay-experiment" || pathname === "/overlay-experiment-page") {
    return <OverlayExperimentPage />;
  }

  if (pathname === "/teen-autonomy") {
    return <TeenAutonomyPage />;
  }

  if (pathname === "/teen-autonomy-figure-1") {
    return <TeenAutonomyFigure1EmbedPage />;
  }

  return <HomePage />;
}
