/** Shapes returned by the zagoat API. */

export type Me = {
  id: string;
  email: string;
  name: string | null;
  avatar_url: string | null;
  code_opt_in: boolean;
  created_at: string;
};
