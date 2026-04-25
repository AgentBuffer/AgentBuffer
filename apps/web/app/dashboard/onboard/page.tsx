import { OnboardingWizard } from "@/components/onboarding/onboarding-wizard";

export default function OnboardPage() {
  return (
    <div className="py-4">
      <h1 className="text-xl font-bold mb-6">Onboard Your Brand</h1>
      <OnboardingWizard />
    </div>
  );
}
