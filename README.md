# xmrauctions

This is a somewhat simple little CRUD, Django app. It's fairly minimal auction house where you can post items you possess and exchange them with your fellow humans from anywhere around the world.

Item creation requires you to provide a Monero wallet address. There are many good options, including but not limited to:

* [CakeWallet](https://twitter.com/cakewalletxmr)
* [MyMonero](https://mymonero.com/)
* [Monerujo](https://www.monerujo.io/)

This app is in an alpha stage and is not polished enough to transact real money. Once we make progress on some of the to-do items we will proceed to that.

## Dev

You first need secrets. Copy the example one and fill in your details. You'll need to provide your own node and wallet RPC endpoints or public ones. The `Makefile` provided should be enough for general use. Review that file to see what's happening under the hood.

```sh
cp env.example .env
vim .env
make build
make up
make dev
```

## Go-Live Checklist

In no particular order, nice to haves, and should likely haves:

- [ ] Bad bot spam prevention (fail2ban)
- [ ] DDoS mitigation
- [ ] Secrets in SSM with env setting
- [ ] Email spam prevention
- [ ] Cloudtrail configured all regions
- [ ] Web server access logs syncing to S3
- [ ] Log rotate on access logs
- [ ] Security ELK dashboard
- [ ] Malicious Image upload abuse prevention
- [ ] SES metric alarms
- [ ] Budget alarms
- [ ] Unit Tests
- [ ] DB backups
- [ ] Dockerize wallet to run on other instance
