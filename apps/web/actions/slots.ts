"use server";

import { createClient } from "@/lib/supabase/server";

export async function getSlots() {
  const supabase = await createClient();

  const { data, error } = await supabase
    .from("content_slots")
    .select("*")
    .order("slot_number", { ascending: true });

  if (error) throw new Error(error.message);
  return data;
}
