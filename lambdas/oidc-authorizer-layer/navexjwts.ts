import { Jwt, JwtPayload } from "jsonwebtoken";

export interface NavexJwtPayload extends JwtPayload {
    clientkey?: string;
    session_state?: string;
    scope?: string;
}
export interface NavexJwt extends Jwt {
    payload: NavexJwtPayload
}
