import React, { useEffect, useState } from "react";
import HomePage from "./pages/HomePage";
import PolishedPage from "./pages/PolishedPage";
import OverlayExperimentPage from "./pages/OverlayExperimentPage";

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

  if (pathname === "/overlay-experiment") {
    return <OverlayExperimentPage />;
  }

  return <HomePage />;
}
