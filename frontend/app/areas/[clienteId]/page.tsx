import { redirect } from "next/navigation";

export default function AreasRootPage({ params }: { params: { clienteId: string } }) {
  redirect(`/areas/${params.clienteId}/130`);
}
