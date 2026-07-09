import HallTemplate from "@modules/customer/templates/hall"
import { Metadata } from "next"

export const metadata: Metadata = {
  title: "Shopping Hall",
  description: "Discover products from different shops.",
}

export default function HallPage() {
  return <HallTemplate />
}
