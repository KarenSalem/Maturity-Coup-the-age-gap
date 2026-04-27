import React, { useEffect, useState } from "react";
import HomePage from "./pages/HomePage";
import PolishedPage from "./pages/PolishedPage";

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

  return <HomePage />;
}
