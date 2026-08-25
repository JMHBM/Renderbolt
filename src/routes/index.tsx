import { createFileRoute } from "@tanstack/react-router";
import { StudioApp } from "@/components/studio/studio-app";

export const Route = createFileRoute("/")({ component: Home });

function Home() {
  return <StudioApp />;
}
