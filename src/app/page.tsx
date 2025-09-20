import { redirect } from 'next/navigation';

export default function RootPage() {
  // Automatically redirect to the analysis page
  redirect('/analysis');
}