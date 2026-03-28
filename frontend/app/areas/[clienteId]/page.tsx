import { redirect } from "next/navigation";

type PageParams = {
  clienteId: string;
};

type PageProps = {
  params: Promise<PageParams>;
  searchParams?: Promise<Record<string, string | string[] | undefined>>;
};

export default async function AreasRootPage({ params }: PageProps) {
  const { clienteId } = await params;
  redirect(`/areas/${clienteId}/130`);
}

export async function generateMetadata({ params }: PageProps) {
  const { clienteId } = await params;
  return {
    title: `Areas - ${clienteId} | SocioAI`,
  };
}
