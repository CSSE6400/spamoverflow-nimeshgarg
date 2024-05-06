import http from "k6/http";
import { sleep, check } from "k6";

export const options = {
  stages: [
    { target: 5000, duration: "1m" },
    //    { target: 5000, duration: '10m' },
  ],
};

export default function () {
  const data = {
    metadata: {
      spamhammer: "1|14",
    },
    contents: {
      subject: "Important information about your account.",
      from: "support@uq.edu.au",
      to: "no-reply@uq.edu.au",
      body: "Dear customer,\nWe have noticed some suspicious activity on your account. Please click [here](https://scam-check.uq.edu.au?userId=uqehugh3) to reset your password. and https://scam-check.uq.edu.au?userId=uqehugh3",
    },
  };
  const res = http.post(
    "http://spamoverflow-1430562822.us-east-1.elb.amazonaws.com:8080/api/v1/customers/111100005412/emails",
    JSON.stringify(data),
    { headers: { "Content-Type": "application/json" } }
  );
  check(res, { "status was 201": (r) => r.status == 201 });
  sleep(1);
}
