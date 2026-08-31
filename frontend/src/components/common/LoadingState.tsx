interface Props { message?: string; }

export default function LoadingState({ message = 'Loading...' }: Props) {
  return (
    <div className="flex flex-col items-center justify-center h-full gap-3 text-gray-400">
      <div className="w-8 h-8 border-2 border-emerald-200 border-t-emerald-500 rounded-full animate-spin" />
      <span className="text-xs">{message}</span>
    </div>
  );
}
