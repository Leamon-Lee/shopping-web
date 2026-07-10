import { redirect } from "next/navigation"
export default async function Legacy(props: { params: Promise<{ username: string }> }) { await props.params; redirect("/manager") }
