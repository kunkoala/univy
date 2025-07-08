import { eq } from "drizzle-orm";
import NextAuth from "next-auth";
import GitHubProvider from "next-auth/providers/github";

import { env } from "@/env.mjs";
import { db, users } from "@/lib/schema";
import { stripeServer } from "@/lib/stripe";

export const { auth, handlers, signIn, signOut } = NextAuth({
  // TODO: Implement database session strategy with fastapi
  session: {
    strategy: "jwt",
    updateAge: 24 * 60 * 60, // this is the update age for the session, in seconds. Explanation: update age is the time after which the session will be updated. If the session is not updated, the user will be logged out.
  },
  providers: [
    GitHubProvider({
      clientId: env.GITHUB_ID,
      clientSecret: env.GITHUB_SECRET,
    }),
  ],
  callbacks: {
    // // This is the database session strategy
    // async session({ session, user }) {
    //   if (!session.user) return session;

    //   session.user.id = user.id;
    //   session.user.stripeCustomerId = user.stripeCustomerId;
    //   session.user.isActive = user.isActive;

    //   return session;
    // },

    async jwt({ token, user }) {
      if (user) {
        token.id = user.id;
        token.stripeCustomerId = user.stripeCustomerId;
        token.isActive = user.isActive;
      }
      return token;
    },
  },
  events: {
    createUser: async ({ user }) => {
      if (!user.email || !user.name) return;

      await stripeServer.customers
        .create({
          email: user.email,
          name: user.name,
        })
        .then(async (customer) =>
          db
            .update(users)
            .set({ stripeCustomerId: customer.id })
            .where(eq(users.id, user.id!)),
        );
    },
  },
  secret: env.AUTH_SECRET,
});
