"use server";

import { createClient } from "@/lib/supabase/server";

export async function createBrand(formData: FormData) {
  const supabase = await createClient();

  const name = formData.get("name") as string;
  const industry = formData.get("industry") as string;
  const tagline = formData.get("tagline") as string;
  const target_audience = formData.get("target_audience") as string;
  const voice_description = formData.get("voice_description") as string;

  const {
    data: { user },
  } = await supabase.auth.getUser();

  if (!user) throw new Error("Unauthorized");

  const orgId = user.user_metadata?.org_id;
  if (!orgId) throw new Error("No org_id in user metadata");

  const brandKit = {
    brand_id: crypto.randomUUID(),
    org_id: orgId,
    name,
    tagline,
    voice_description,
    target_audience,
    color_palette: [],
    logo_url: null,
    sample_captions: [],
    industry,
  };

  const { data, error } = await supabase
    .from("brands")
    .insert({
      org_id: orgId,
      name,
      brand_kit: brandKit,
    })
    .select()
    .single();

  if (error) throw new Error(error.message);
  return data;
}
