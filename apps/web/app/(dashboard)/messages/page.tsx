import { MessageFeed } from "@/components/messages/message-feed";

export default function MessagesPage() {
  return (
    <div className="py-4 max-w-2xl">
      <h1 className="text-xl font-bold mb-6">Agent Activity</h1>
      <MessageFeed />
    </div>
  );
}
