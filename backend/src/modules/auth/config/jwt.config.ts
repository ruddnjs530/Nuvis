export default () => ({
  jwt: {
    secret: process.env.SECRET_KEY,
    signOptions: {
      expiresIn: 3600 * 24 * 31,
    },
  },
});
