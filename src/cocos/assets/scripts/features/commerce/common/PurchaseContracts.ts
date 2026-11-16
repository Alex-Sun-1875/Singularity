/** Business contracts only; this module does not authorize grants or simulate a payment. */
export type PaymentEnvironment='sandbox'|'production';
export type MaterialKind='gold'|'iron'|'gemShards'|'socketTools'|'runes'|'cores';
export interface MaterialQuantity {readonly kind:MaterialKind;readonly quantity:number}
export interface MaterialProduct {
 readonly productId:string;
 readonly version:number;
 readonly category:'forging'|'gems'|'sockets';
 readonly nameKey:string;
 readonly priceFen:number;
 readonly materials:readonly MaterialQuantity[];
 readonly chapter:number;
 readonly weeklyLimit:number;
}
export interface PurchaseIdentity {
 readonly accountId:string;
 readonly journeyId:string;
 readonly appId:string;
 readonly environment:PaymentEnvironment;
}
export type OrderStatus='created'|'confirming'|'paid'|'delivered'|'closed'|'refunding'|'refunded';
export interface MaterialOrder {
 readonly orderId:string;
 readonly identity:PurchaseIdentity;
 readonly productId:string;
 readonly productVersion:number;
 readonly quantity:number;
 readonly priceFen:number;
 readonly status:OrderStatus;
 readonly deliveryId?:string;
}
export interface PaymentCapability {
 readonly available:boolean;
 readonly reason:'ready'|'unsupported'|'identity-required'|'service-unavailable'|'not-enabled';
}
/** Must be backed by a validated account and a server ledger before it is registered. */
export interface MaterialPurchaseService {
 capability():PaymentCapability;
 products():Promise<readonly MaterialProduct[]>;
 purchase(productId:string,identity:PurchaseIdentity):Promise<MaterialOrder>;
 order(orderId:string):Promise<MaterialOrder>;
 restore(identity:PurchaseIdentity):Promise<readonly MaterialOrder[]>;
}
